"""
services/collector_manager.py

Centralny menedżer collectorów.

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
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable

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
# TYPE ALIAS
# ==========================================================

CollectorCallable = Callable[[], object]


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
        tylko potrzebne collectory
    """

    def __init__(
        self,
        state: DashboardState | None = None,
    ) -> None:

        self.state = (
            state
            or DashboardState()
        )

        self._collectors: dict[
            str,
            tuple[
                CollectorCallable,
                Callable[[], float],
            ],
        ] = {
            "cpu": (
                cpu_collector.collect,
                lambda: config.CPU_INTERVAL,
            ),
            "memory": (
                memory_collector.collect,
                lambda: config.RAM_INTERVAL,
            ),
            "network": (
                network_collector.collect,
                lambda: config.NETWORK_INTERVAL,
            ),
            "temperature": (
                sensor_collector.collect,
                lambda: config.TEMPERATURE_INTERVAL,
            ),
            "fan": (
                fan_collector.collect,
                lambda: config.FAN_INTERVAL,
            ),
            "storage": (
                storage_collector.collect,
                lambda: config.DISK_INTERVAL,
            ),
            "nvme": (
                nvme_collector.collect,
                lambda: config.NVME_INTERVAL,
            ),
            "system": (
                system_collector.collect,
                lambda: config.SYSTEM_INTERVAL,
            ),
            "proxmox": (
                proxmox_collector.collect,
                lambda: config.PROXMOX_INTERVAL,
            ),
            "pihole": (
                pihole_collector.collect,
                lambda: config.PIHOLE_INTERVAL,
            ),
        }

    # ======================================================
    # ERROR HANDLING
    # ======================================================

    def _handle_error(
        self,
        collector_name: str,
        exception: Exception,
    ) -> None:
        """
        Rejestruje błąd pojedynczego collectora.

        Błąd jednego źródła danych nie może zatrzymać
        całego dashboardu.
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

        cache.set_error(
            collector_name,
            error_message,
        )

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
            # Problem z logiem nie może
            # zatrzymać dashboardu.
            pass

    # ======================================================
    # SHOULD UPDATE
    # ======================================================

    @staticmethod
    def _should_update(
        name: str,
        interval: float,
    ) -> bool:
        """
        Sprawdza centralny cache.
        """

        return cache.needs_update(
            name,
            interval,
        )

    # ======================================================
    # COLLECTOR ENABLED
    # ======================================================

    @staticmethod
    def _collector_enabled(
        name: str,
    ) -> bool:
        """
        Sprawdza, czy collector powinien działać.

        Integracje UI można wyłączyć przez config.py.
        """

        if name == "proxmox":
            return getattr(
                config,
                "SHOW_PROXMOX_PANEL",
                True,
            )

        if name == "pihole":
            return getattr(
                config,
                "SHOW_PIHOLE_PANEL",
                True,
            )

        return True

    # ======================================================
    # UPDATE CPU
    # ======================================================

    def _update_cpu(self) -> None:
        """
        Aktualizuje CPU.
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
    # UPDATE MEMORY
    # ======================================================

    def _update_memory(self) -> None:
        """
        Aktualizuje RAM i SWAP.

        Aktualny MemoryInfo zawiera również
        informacje o SWAP, dlatego collector
        zwraca jeden obiekt MemoryInfo.
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
    # UPDATE NETWORK
    # ======================================================

    def _update_network(self) -> None:
        """
        Aktualizuje sieć.
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
    # UPDATE TEMPERATURE
    # ======================================================

    def _update_temperature(self) -> None:
        """
        Aktualizuje temperatury.
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

            # Synchronizacja temperatury CPU
            # z modelem CPU.
            if (
                info.cpu > 0
                and self.state.cpu is not None
            ):
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
    # UPDATE FAN
    # ======================================================

    def _update_fan(self) -> None:
        """
        Aktualizuje wentylator.

        WAŻNE:
        Fan używa własnego FAN_INTERVAL.
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
    # UPDATE STORAGE
    # ======================================================

    def _update_storage(self) -> None:
        """
        Aktualizuje systemy plików.
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
    # UPDATE NVME
    # ======================================================

    def _update_nvme(self) -> None:
        """
        Aktualizuje NVMe.
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
    # UPDATE SYSTEM
    # ======================================================

    def _update_system(self) -> None:
        """
        Aktualizuje informacje systemowe.
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
    # UPDATE PROXMOX
    # ======================================================

    def _update_proxmox(self) -> None:
        """
        Aktualizuje Proxmox.
        """

        name = "proxmox"

        if not self._collector_enabled(name):
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
    # UPDATE PI-HOLE
    # ======================================================

    def _update_pihole(self) -> None:
        """
        Aktualizuje Pi-hole.
        """

        name = "pihole"

        if not self._collector_enabled(name):
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

        Każdy collector ma niezależny harmonogram.
        """

        now = time.monotonic()

        self._update_cpu()
        self._update_memory()
        self._update_network()

        self._update_temperature()
        self._update_fan()
        self._update_system()

        self._update_storage()
        self._update_nvme()

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

        Czyszczenie cache powoduje, że każdy collector
        zostanie potraktowany jako wymagający aktualizacji.
        """

        cache.clear()

        return self.update()


# ==========================================================
# GLOBAL MANAGER
# ==========================================================

collector_manager = CollectorManager()