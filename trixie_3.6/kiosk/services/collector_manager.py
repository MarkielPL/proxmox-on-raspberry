"""
services/collector_manager.py

Centralny manager danych dashboardu.

Odpowiada za:

    collectors
        ↓
    cache
        ↓
    DashboardState

Manager kontroluje częstotliwość wykonywania
poszczególnych collectorów zgodnie z config.py.

Przykładowe interwały:

    CPU          → 1 s
    RAM          → 2 s
    Network      → 1 s
    Temperature  → 5 s
    Disk         → 60 s
    NVMe         → 5 s
    Fan          → 2 s
    Proxmox      → 5 s
    Pi-hole      → 10 s

Żaden panel Rich nie jest tworzony w tym module.
"""

from __future__ import annotations

import time
import traceback
from typing import Callable
from typing import Any

import config

from models import DashboardState

from collectors.cpu import cpu_collector
from collectors.memory import memory_collector
from collectors.network import network_collector
from collectors.nvme import nvme_collector
from collectors.pihole import pihole_collector
from collectors.proxmox import proxmox_collector
from collectors.system import system_collector
from collectors.storage import storage_collector
from collectors.fan import fan_collector
from collectors.sensors import sensors_collector

from services.cache import DataCache
from services.cache import cache


class CollectorManager:
    """
    Centralny manager wszystkich collectorów.
    """

    def __init__(
        self,
        data_cache: DataCache | None = None,
    ) -> None:

        self.cache = (
            data_cache
            or cache
        )

        self.state = (
            DashboardState()
        )

        self.last_error = ""

        self.error_count = 0

    # ======================================================
    # SAFE COLLECT
    # ======================================================

    def _collect_safe(
        self,
        key: str,
        collector: Callable[
            [],
            Any,
        ],
    ) -> Any | None:
        """
        Wykonuje collector w bezpieczny sposób.

        Jeżeli collector zakończy się błędem:

        - dashboard nie zostaje zatrzymany,
        - ostatnia poprawna wartość pozostaje
          w cache,
        - błąd zostaje zapisany.
        """

        try:

            value = collector()

            self.cache.set(
                key,
                value,
            )

            return value

        except Exception as exc:

            error = (
                f"{key}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            self.cache.set_error(
                key,
                error,
            )

            self.last_error = error

            self.error_count += 1

            if getattr(
                config,
                "ENABLE_LOGGING",
                True,
            ):

                self._log_error(
                    error
                )

            return self.cache.get(
                key
            )

    # ======================================================
    # LOG ERROR
    # ======================================================

    @staticmethod
    def _log_error(
        message: str,
    ) -> None:
        """
        Zapisuje błąd do pliku log.
        """

        try:

            log_dir = config.LOG_DIR

            log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            timestamp = time.strftime(
                config.DATETIME_FORMAT
            )

            with config.LOG_FILE.open(
                "a",
                encoding="utf-8",
            ) as logfile:

                logfile.write(
                    f"[{timestamp}] "
                    f"{message}\n"
                )

        except OSError:

            # Błąd logowania nie może
            # zatrzymać dashboardu.
            pass

    # ======================================================
    # UPDATE IF NEEDED
    # ======================================================

    def _update_if_needed(
        self,
        key: str,
        interval: float,
        collector: Callable[
            [],
            Any,
        ],
    ) -> Any | None:
        """
        Aktualizuje dane tylko wtedy,
        gdy upłynął odpowiedni interwał.
        """

        if not self.cache.needs_update(
            key,
            interval,
        ):

            return self.cache.get(
                key
            )

        return self._collect_safe(
            key,
            collector,
        )

    # ======================================================
    # CPU
    # ======================================================

    def _update_cpu(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "cpu",
            config.CPU_INTERVAL,
            cpu_collector.collect,
        )

        if value is None:
            return

        self.state.cpu = value

        self.state.cpu_updated = now

    # ======================================================
    # MEMORY
    # ======================================================

    def _update_memory(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "memory",
            config.RAM_INTERVAL,
            memory_collector.collect,
        )

        if value is None:
            return

        memory, swap = value

        self.state.memory = memory

        self.state.swap = swap

        self.state.memory_updated = now

    # ======================================================
    # NETWORK
    # ======================================================

    def _update_network(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "network",
            config.NETWORK_INTERVAL,
            network_collector.collect,
        )

        if value is None:
            return

        self.state.network = value

        self.state.network_updated = now

    # ======================================================
    # TEMPERATURE
    # ======================================================

    def _update_temperature(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "temperature",
            config.TEMPERATURE_INTERVAL,
            sensors_collector.collect,
        )

        if value is None:
            return

        self.state.temperatures = value

        self.state.temperature_updated = now

    # ======================================================
    # STORAGE
    # ======================================================

    def _update_storage(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "storage",
            config.DISK_INTERVAL,
            storage_collector.collect,
        )

        if value is None:
            return

        self.state.disks = value

        self.state.storage_updated = now

    # ======================================================
    # NVMe
    # ======================================================

    def _update_nvme(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "nvme",
            config.NVME_INTERVAL,
            nvme_collector.collect,
        )

        if value is None:
            return

        self.state.nvme = value

        self.state.nvme_updated = now

    # ======================================================
    # FAN
    # ======================================================

    def _update_fan(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "fan",
            config.LIVE_REFRESH,
            fan_collector.collect,
        )

        if value is None:
            return

        self.state.fan = value

        self.state.fan_updated = now

    # ======================================================
    # SYSTEM
    # ======================================================

    def _update_system(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "system",
            config.SYSTEM_INTERVAL,
            system_collector.collect,
        )

        if value is None:
            return

        self.state.system = value

        self.state.system_updated = now

    # ======================================================
    # PROXMOX
    # ======================================================

    def _update_proxmox(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "proxmox",
            config.PROXMOX_INTERVAL,
            proxmox_collector.collect,
        )

        if value is None:
            return

        self.state.proxmox = value

        self.state.proxmox_updated = now

    # ======================================================
    # PI-HOLE
    # ======================================================

    def _update_pihole(
        self,
        now: float,
    ) -> None:

        value = self._update_if_needed(
            "pihole",
            config.PIHOLE_INTERVAL,
            pihole_collector.collect,
        )

        if value is None:
            return

        self.state.pihole = value

        self.state.pihole_updated = now

    # ======================================================
    # UPDATE
    # ======================================================

    def update(
        self,
    ) -> DashboardState:
        """
        Aktualizuje cały stan dashboardu.

        Wywołanie tej metody może następować
        przy każdym odświeżeniu UI.
        Cache zdecyduje, które collectory
        rzeczywiście zostaną uruchomione.
        """

        now = time.monotonic()

        # --------------------------------------------------
        # SYSTEM
        # --------------------------------------------------

        self._update_system(
            now
        )

        # --------------------------------------------------
        # CPU
        # --------------------------------------------------

        self._update_cpu(
            now
        )

        # --------------------------------------------------
        # RAM
        # --------------------------------------------------

        self._update_memory(
            now
        )

        # --------------------------------------------------
        # NETWORK
        # --------------------------------------------------

        self._update_network(
            now
        )

        # --------------------------------------------------
        # TEMPERATURE
        # --------------------------------------------------

        self._update_temperature(
            now
        )

        # --------------------------------------------------
        # STORAGE
        # --------------------------------------------------

        self._update_storage(
            now
        )

        # --------------------------------------------------
        # NVMe
        # --------------------------------------------------

        self._update_nvme(
            now
        )

        # --------------------------------------------------
        # FAN
        # --------------------------------------------------

        self._update_fan(
            now
        )

        # --------------------------------------------------
        # PROXMOX
        # --------------------------------------------------

        if getattr(
            config,
            "SHOW_PROXMOX_PANEL",
            True,
        ):

            self._update_proxmox(
                now
            )

        # --------------------------------------------------
        # PI-HOLE
        # --------------------------------------------------

        if getattr(
            config,
            "SHOW_PIHOLE_PANEL",
            True,
        ):

            self._update_pihole(
                now
            )

        # --------------------------------------------------
        # GLOBAL STATE
        # --------------------------------------------------

        self.state.last_update = now

        self.state.error_count = (
            self.error_count
        )

        self.state.last_error = (
            self.last_error
        )

        return self.state

    # ======================================================
    # FORCE UPDATE
    # ======================================================

    def force_update(
        self,
        key: str | None = None,
    ) -> DashboardState:
        """
        Wymusza aktualizację jednego źródła
        albo wszystkich źródeł.

        Przydatne podczas diagnostyki.
        """

        if key is None:

            self.cache.clear()

        else:

            self.cache.clear(
                key
            )

        return self.update()


# ==========================================================
# GLOBALNY MANAGER
# ==========================================================

collector_manager = (
    CollectorManager()
)