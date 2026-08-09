"""
services/collector_manager.py

Centralny menedżer collectorów.

Architektura:

    collectors/
        ↓
    services/cache.py
        ↓
    CollectorManager
        ↓
    DashboardState
        ↓
    panels.py
        ↓
    dashboard.py

CollectorManager:

    - uruchamia collectory,
    - respektuje interwały z config.py,
    - korzysta z centralnego DataCache,
    - aktualizuje DashboardState,
    - izoluje błędy pojedynczych collectorów,
    - zachowuje ostatnie poprawne dane po błędzie,
    - nie zawiera logiki UI.

WAŻNE:

Interwały nie są przechowywane tutaj.

Za kontrolę czasu aktualizacji odpowiada:

    services/cache.py

Dzięki temu nie mamy dwóch niezależnych
mechanizmów odmierzania czasu.
"""

from __future__ import annotations

import time
import traceback

import config

from models import DashboardState

from collectors.cpu import cpu_collector
from collectors.fan import fan_collector
from collectors.memory import memory_collector
from collectors.network import network_collector
from collectors.nvme import nvme_collector
from collectors.pihole import pihole_collector
from collectors.proxmox import proxmox_collector
from collectors.sensors import sensor_collector
from collectors.storage import storage_collector
from collectors.system import system_collector

from services.cache import cache


# ==========================================================
# COLLECTOR MANAGER
# ==========================================================

class CollectorManager:
    """
    Centralny menedżer danych dashboardu.

    Manager odpowiada za:

        1. sprawdzenie cache,
        2. uruchomienie collectora,
        3. zapis poprawnego wyniku,
        4. aktualizację DashboardState,
        5. obsługę błędów.

    Manager nie odpowiada za:

        - wygląd paneli,
        - Rich,
        - formatowanie tekstu,
        - layout dashboardu.
    """

    def __init__(
        self,
        state: DashboardState | None = None,
    ) -> None:

        self.state = (
            state
            or DashboardState()
        )

    # ======================================================
    # ERROR HANDLING
    # ======================================================

    def _handle_error(
        self,
        collector_name: str,
        exception: Exception,
    ) -> None:
        """
        Rejestruje błąd collectora.

        Błąd jednego źródła danych nie może
        zatrzymać całego dashboardu.

        Ostatnia poprawna wartość pozostaje
        w cache.
        """

        error_message = (
            f"{collector_name}: "
            f"{type(exception).__name__}: "
            f"{exception}"
        )

        self.state.error_count += 1

        self.state.last_error = (
            error_message
        )

        # --------------------------------------------------
        # Zapis błędu w cache.
        # --------------------------------------------------

        cache.set_error(
            collector_name,
            error_message,
        )

        # --------------------------------------------------
        # Logowanie.
        # --------------------------------------------------

        if not getattr(
            config,
            "ENABLE_LOGGING",
            False,
        ):
            return

        try:

            config.LOG_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            with open(
                config.LOG_FILE,
                "a",
                encoding="utf-8",
            ) as log:

                timestamp = time.strftime(
                    config.DATETIME_FORMAT
                )

                log.write(
                    f"[{timestamp}] "
                    f"{error_message}\n"
                )

                log.write(
                    traceback.format_exc()
                )

                log.write("\n")

        except OSError:
            # Błąd zapisu logu nie może
            # zatrzymać dashboardu.
            pass

    # ======================================================
    # CACHE CHECK
    # ======================================================

    @staticmethod
    def _should_update(
        name: str,
        interval: float,
    ) -> bool:
        """
        Sprawdza przez centralny cache,
        czy collector powinien zostać wykonany.
        """

        return cache.needs_update(
            name,
            interval,
        )

    # ======================================================
    # CPU
    # ======================================================

    def _update_cpu(self) -> None:
        """
        Aktualizuje informacje o CPU.
        """

        if not self._should_update(
            "cpu",
            config.CPU_INTERVAL,
        ):
            return

        try:

            info = (
                cpu_collector.collect()
            )

            # --------------------------------------------------
            # Cache
            # --------------------------------------------------

            cache.set(
                "cpu",
                info,
            )

            # --------------------------------------------------
            # Dashboard state
            # --------------------------------------------------

            self.state.cpu = info

            self.state.cpu_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "cpu",
                exc,
            )

    # ======================================================
    # MEMORY
    # ======================================================

    def _update_memory(self) -> None:
        """
        Aktualizuje informacje o RAM i SWAP.
        """

        if not self._should_update(
            "memory",
            config.RAM_INTERVAL,
        ):
            return

        try:

            memory, swap = (
                memory_collector.collect()
            )

            # --------------------------------------------------
            # Cache RAM
            # --------------------------------------------------

            cache.set(
                "memory",
                memory,
            )

            # --------------------------------------------------
            # Cache SWAP
            # --------------------------------------------------

            cache.set(
                "swap",
                swap,
            )

            # --------------------------------------------------
            # Dashboard state
            # --------------------------------------------------

            self.state.memory = memory

            # --------------------------------------------------
            # Synchronizacja SWAP.
            #
            # models.py posiada pola SWAP
            # w MemoryInfo.
            # --------------------------------------------------

            self.state.memory.swap_total = (
                swap.total
            )

            self.state.memory.swap_used = (
                swap.used
            )

            self.state.memory.swap_free = (
                swap.free
            )

            self.state.memory.swap_percent = (
                swap.percent
            )

            self.state.memory_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "memory",
                exc,
            )

    # ======================================================
    # NETWORK
    # ======================================================

    def _update_network(self) -> None:
        """
        Aktualizuje informacje sieciowe.
        """

        if not self._should_update(
            "network",
            config.NETWORK_INTERVAL,
        ):
            return

        try:

            info = (
                network_collector.collect()
            )

            cache.set(
                "network",
                info,
            )

            self.state.network = info

            self.state.network_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "network",
                exc,
            )

    # ======================================================
    # TEMPERATURE
    # ======================================================

    def _update_temperature(self) -> None:
        """
        Aktualizuje wszystkie czujniki temperatury.
        """

        if not self._should_update(
            "temperature",
            config.TEMPERATURE_INTERVAL,
        ):
            return

        try:

            info = (
                sensor_collector.collect()
            )

            cache.set(
                "temperature",
                info,
            )

            self.state.temperatures = info

            # --------------------------------------------------
            # Synchronizacja CPU temperature.
            # --------------------------------------------------

            if (
                info.cpu > 0
            ):

                self.state.cpu.temperature = (
                    info.cpu
                )

            self.state.temperature_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "temperature",
                exc,
            )

    # ======================================================
    # STORAGE
    # ======================================================

    def _update_storage(self) -> None:
        """
        Aktualizuje informacje o systemach plików.
        """

        if not self._should_update(
            "storage",
            config.DISK_INTERVAL,
        ):
            return

        try:

            info = (
                storage_collector.collect()
            )

            cache.set(
                "storage",
                info,
            )

            self.state.disks = info

            self.state.storage_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "storage",
                exc,
            )

    # ======================================================
    # NVME
    # ======================================================

    def _update_nvme(self) -> None:
        """
        Aktualizuje informacje o NVMe.
        """

        if not self._should_update(
            "nvme",
            config.NVME_INTERVAL,
        ):
            return

        try:

            info = (
                nvme_collector.collect()
            )

            cache.set(
                "nvme",
                info,
            )

            self.state.nvme = info

            self.state.nvme_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "nvme",
                exc,
            )

    # ======================================================
    # FAN
    # ======================================================

    def _update_fan(self) -> None:
        """
        Aktualizuje informacje o wentylatorze.
        """

        if not self._should_update(
            "fan",
            config.TEMPERATURE_INTERVAL,
        ):
            return

        try:

            info = (
                fan_collector.collect()
            )

            cache.set(
                "fan",
                info,
            )

            self.state.fan = info

            self.state.fan_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "fan",
                exc,
            )

    # ======================================================
    # SYSTEM
    # ======================================================

    def _update_system(self) -> None:
        """
        Aktualizuje informacje o systemie.
        """

        if not self._should_update(
            "system",
            config.SYSTEM_INTERVAL,
        ):
            return

        try:

            info = (
                system_collector.collect()
            )

            cache.set(
                "system",
                info,
            )

            self.state.system = info

            self.state.system_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "system",
                exc,
            )

    # ======================================================
    # PROXMOX
    # ======================================================

    def _update_proxmox(self) -> None:
        """
        Aktualizuje informacje o Proxmox VE.
        """

        if not getattr(
            config,
            "SHOW_PROXMOX_PANEL",
            True,
        ):
            return

        if not self._should_update(
            "proxmox",
            config.PROXMOX_INTERVAL,
        ):
            return

        try:

            info = (
                proxmox_collector.collect()
            )

            cache.set(
                "proxmox",
                info,
            )

            self.state.proxmox = info

            self.state.proxmox_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "proxmox",
                exc,
            )

    # ======================================================
    # PI-HOLE
    # ======================================================

    def _update_pihole(self) -> None:
        """
        Aktualizuje informacje o Pi-hole.
        """

        if not getattr(
            config,
            "SHOW_PIHOLE_PANEL",
            True,
        ):
            return

        if not self._should_update(
            "pihole",
            config.PIHOLE_INTERVAL,
        ):
            return

        try:

            info = (
                pihole_collector.collect()
            )

            cache.set(
                "pihole",
                info,
            )

            self.state.pihole = info

            self.state.pihole_updated = (
                time.monotonic()
            )

        except Exception as exc:

            self._handle_error(
                "pihole",
                exc,
            )

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self) -> DashboardState:
        """
        Aktualizuje wszystkie źródła,
        których interwał już minął.

        Zwraca aktualny DashboardState.

        Ponieważ każdy collector posiada własny
        wpis cache, collectory mogą działać
        z niezależnymi częstotliwościami.
        """

        now = time.monotonic()

        # --------------------------------------------------
        # Collectory szybkie
        # --------------------------------------------------

        self._update_cpu()

        self._update_memory()

        self._update_network()

        # --------------------------------------------------
        # Collectory średniej częstotliwości
        # --------------------------------------------------

        self._update_temperature()

        self._update_fan()

        self._update_system()

        # --------------------------------------------------
        # Collectory wolniejsze
        # --------------------------------------------------

        self._update_storage()

        self._update_nvme()

        self._update_proxmox()

        self._update_pihole()

        # --------------------------------------------------
        # Globalny timestamp.
        # --------------------------------------------------

        self.state.last_update = now

        self.state.running = True

        return self.state

    # ======================================================
    # FORCE UPDATE
    # ======================================================

    def force_update(self) -> DashboardState:
        """
        Wymusza natychmiastową aktualizację
        wszystkich collectorów.

        Nie posiada własnego mechanizmu czasu.

        Po prostu czyści cache aktualizacji,
        dzięki czemu needs_update() zwróci True.
        """

        cache.clear()

        return self.update()


# ==========================================================
# GLOBALNY MANAGER
# ==========================================================

collector_manager = CollectorManager()