"""
Centralny menedżer collectorów Raspberry Pi Kiosk Dashboard.

Odpowiada za:

- uruchamianie collectorów,
- respektowanie interwałów z config.py,
- korzystanie z centralnego DataCache,
- aktualizację DashboardState,
- obsługę błędów,
- logowanie błędów.

Manager NIE odpowiada za:

- Rich,
- Textual,
- wygląd UI,
- layout,
- formatowanie prezentacji.

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

    Główna zasada:

        UI refresh
             ↓
        CollectorManager
             ↓
        cache.needs_update()
             ↓
        tylko collectory, których interwał minął

    Manager:

    - nie wykonuje logiki UI,
    - nie zna Rich,
    - nie zna layoutu,
    - izoluje błędy collectorów,
    - zachowuje ostatnie poprawne dane.
    """

    def __init__(
        self,
        state: DashboardState | None = None,
    ) -> None:

        self.state = (
            state
            if state is not None
            else DashboardState()
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
        w cache i DashboardState.
        """

        error_message = (
            f"{collector_name}: "
            f"{type(exception).__name__}: "
            f"{exception}"
        )

        self.state.error_count += 1
        self.state.last_error = error_message

        # --------------------------------------------------
        # Cache
        # --------------------------------------------------

        cache.set_error(
            collector_name,
            error_message,
        )

        # --------------------------------------------------
        # Logowanie
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
            # Problem z logowaniem nie może
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

        name = "cpu"

        if not self._should_update(
            name,
            config.CPU_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = cpu_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.cpu = info

            self.state.cpu_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # MEMORY
    # ======================================================

    def _update_memory(self) -> None:
        """
        Aktualizuje informacje o RAM oraz SWAP.

        Aktualny MemoryInfo zawiera zarówno:

        - RAM,
        - SWAP.

        Dlatego collector zwraca jeden obiekt
        MemoryInfo.
        """

        name = "memory"

        if not self._should_update(
            name,
            config.RAM_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = memory_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.memory = info

            self.state.memory_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # NETWORK
    # ======================================================

    def _update_network(self) -> None:
        """
        Aktualizuje informacje sieciowe.
        """

        name = "network"

        if not self._should_update(
            name,
            config.NETWORK_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = network_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.network = info

            self.state.network_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # TEMPERATURE
    # ======================================================

    def _update_temperature(self) -> None:
        """
        Aktualizuje wszystkie czujniki temperatury.
        """

        name = "temperature"

        if not self._should_update(
            name,
            config.TEMPERATURE_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = sensor_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.temperatures = info

            # --------------------------------------------------
            # Synchronizacja temperatury CPU.
            # --------------------------------------------------

            if info.cpu > 0:
                self.state.cpu.temperature = (
                    info.cpu
                )

            self.state.temperature_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # FAN
    # ======================================================

    def _update_fan(self) -> None:
        """
        Aktualizuje informacje o wentylatorze.

        Wentylator posiada własny interwał:
        FAN_INTERVAL.
        """

        name = "fan"

        if not self._should_update(
            name,
            config.FAN_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = fan_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.fan = info

            self.state.fan_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # STORAGE
    # ======================================================

    def _update_storage(self) -> None:
        """
        Aktualizuje informacje o systemach plików.
        """

        name = "storage"

        if not self._should_update(
            name,
            config.DISK_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = storage_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.disks = info

            self.state.storage_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # NVME
    # ======================================================

    def _update_nvme(self) -> None:
        """
        Aktualizuje informacje o NVMe.
        """

        name = "nvme"

        if not self._should_update(
            name,
            config.NVME_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = nvme_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.nvme = info

            self.state.nvme_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # SYSTEM
    # ======================================================

    def _update_system(self) -> None:
        """
        Aktualizuje informacje o systemie.
        """

        name = "system"

        if not self._should_update(
            name,
            config.SYSTEM_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = system_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.system = info

            self.state.system_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # PROXMOX
    # ======================================================

    def _update_proxmox(self) -> None:
        """
        Aktualizuje informacje o Proxmox VE.
        """

        name = "proxmox"

        if not getattr(
            config,
            "SHOW_PROXMOX_PANEL",
            True,
        ):
            return

        if not self._should_update(
            name,
            config.PROXMOX_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = proxmox_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.proxmox = info

            self.state.proxmox_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # PI-HOLE
    # ======================================================

    def _update_pihole(self) -> None:
        """
        Aktualizuje informacje o Pi-hole.
        """

        name = "pihole"

        if not getattr(
            config,
            "SHOW_PIHOLE_PANEL",
            True,
        ):
            return

        if not self._should_update(
            name,
            config.PIHOLE_INTERVAL,
        ):
            return

        cache.mark_attempt(name)

        try:
            info = pihole_collector.collect()

            cache.set(
                name,
                info,
            )

            self.state.pihole = info

            self.state.pihole_updated = (
                time.monotonic()
            )

        except Exception as exc:
            self._handle_error(
                name,
                exc,
            )

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self) -> DashboardState:
        """
        Aktualizuje tylko te źródła danych,
        których interwał już minął.

        Każdy collector posiada niezależny
        harmonogram.
        """

        now = time.monotonic()

        # --------------------------------------------------
        # Szybkie
        # --------------------------------------------------

        self._update_cpu()
        self._update_memory()
        self._update_network()

        # --------------------------------------------------
        # Średnie
        # --------------------------------------------------

        self._update_temperature()
        self._update_fan()
        self._update_system()

        # --------------------------------------------------
        # Wolniejsze
        # --------------------------------------------------

        self._update_storage()
        self._update_nvme()

        # --------------------------------------------------
        # Usługi
        # --------------------------------------------------

        self._update_proxmox()
        self._update_pihole()

        self.state.last_update = now
        self.state.running = True

        return self.state

    # ======================================================
    # FORCE UPDATE
    # ======================================================

    def force_update(self) -> DashboardState:
        """
        Wymusza aktualizację wszystkich collectorów.
        """

        cache.clear()

        return self.update()


# ==========================================================
# GLOBAL INSTANCE
# ==========================================================

collector_manager = CollectorManager()