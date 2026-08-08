"""
Warstwa cache dla Raspberry Pi Kiosk Dashboard.

Odpowiada za:

- przechowywanie ostatnich danych,
- kontrolowanie interwałów odświeżania,
- wywoływanie collectorów tylko wtedy,
  gdy wymagają tego ustawienia w config.py,
- obsługę błędów pojedynczych collectorów.

Dashboard nie powinien bezpośrednio odpytwać
systemu ani usług.

Przepływ:

    collectors
        ↓
      cache
        ↓
    DashboardState
        ↓
      panels
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import config

from models import DashboardState

from collectors.cpu import cpu_collector
from collectors.memory import memory_collector
from collectors.sensors import temperature_collector
from collectors.network import network_collector
from collectors.storage import storage_collector
from collectors.fan import fan_collector
from collectors.proxmox import proxmox_collector
from collectors.pihole import pihole_collector


class DashboardCache:
    """
    Zarządza danymi dashboardu i ich częstotliwością
    aktualizacji.
    """

    def __init__(self) -> None:

        self.state = DashboardState()

        self._last_update: dict[str, float] = {}

        self._initialized = False

    # ======================================================
    # POMOCNICZE
    # ======================================================

    def _is_due(
        self,
        name: str,
        interval: float,
        now: float,
    ) -> bool:
        """
        Sprawdza, czy dane wymagają odświeżenia.
        """

        last_update = self._last_update.get(
            name,
            0.0,
        )

        if not self._initialized:
            return True

        return (
            now - last_update
            >= interval
        )

    # ------------------------------------------------------

    def _mark_updated(
        self,
        name: str,
        now: float,
    ) -> None:
        """
        Zapamiętuje czas aktualizacji.
        """

        self._last_update[name] = now

    # ======================================================
    # BEZPIECZNE WYWOŁANIE COLLECTORA
    # ======================================================

    def _collect(
        self,
        name: str,
        collector: Callable[[], Any],
        now: float,
        interval: float,
        state_attribute: str,
        timestamp_attribute: str,
    ) -> None:
        """
        Wspólna obsługa wszystkich collectorów.

        Błąd jednego collectora nie zatrzymuje dashboardu.
        """

        if not self._is_due(
            name,
            interval,
            now,
        ):
            return

        try:

            result = collector()

            setattr(
                self.state,
                state_attribute,
                result,
            )

            setattr(
                self.state,
                timestamp_attribute,
                now,
            )

            self._mark_updated(
                name,
                now,
            )

        except Exception as error:

            self.state.error_count += 1

            self.state.last_error = (
                f"{name}: {error}"
            )

            # Nie kasujemy poprzednich danych.
            #
            # Dashboard nadal pokazuje ostatni
            # poprawny odczyt.

            self._mark_updated(
                name,
                now,
            )

    # ======================================================
    # AKTUALIZACJA
    # ======================================================

    def update(self) -> DashboardState:
        """
        Aktualizuje dane wymagające odświeżenia.

        Zwraca aktualny DashboardState.
        """

        now = time.monotonic()

        # --------------------------------------------------
        # CPU
        # --------------------------------------------------

        self._collect(
            name="cpu",
            collector=cpu_collector.collect,
            now=now,
            interval=config.CPU_INTERVAL,
            state_attribute="cpu",
            timestamp_attribute="cpu_updated",
        )

        # --------------------------------------------------
        # RAM
        # --------------------------------------------------

        self._collect(
            name="memory",
            collector=memory_collector.collect,
            now=now,
            interval=config.RAM_INTERVAL,
            state_attribute="memory",
            timestamp_attribute="memory_updated",
        )

        # --------------------------------------------------
        # TEMPERATURY
        # --------------------------------------------------

        self._collect(
            name="temperature",
            collector=temperature_collector.collect,
            now=now,
            interval=config.TEMPERATURE_INTERVAL,
            state_attribute="temperatures",
            timestamp_attribute="temperature_updated",
        )

        # --------------------------------------------------
        # NETWORK
        # --------------------------------------------------

        self._collect(
            name="network",
            collector=network_collector.collect,
            now=now,
            interval=config.NETWORK_INTERVAL,
            state_attribute="network",
            timestamp_attribute="network_updated",
        )

        # --------------------------------------------------
        # STORAGE
        # --------------------------------------------------

        self._collect(
            name="storage",
            collector=storage_collector.collect,
            now=now,
            interval=config.DISK_INTERVAL,
            state_attribute="disks",
            timestamp_attribute="storage_updated",
        )

        # --------------------------------------------------
        # FAN
        # --------------------------------------------------

        self._collect(
            name="fan",
            collector=fan_collector.collect,
            now=now,
            interval=config.FAN_INTERVAL,
            state_attribute="fan",
            timestamp_attribute="fan_updated",
        )

        # --------------------------------------------------
        # PROXMOX
        # --------------------------------------------------

        self._collect(
            name="proxmox",
            collector=proxmox_collector.collect,
            now=now,
            interval=config.PROXMOX_INTERVAL,
            state_attribute="proxmox",
            timestamp_attribute="proxmox_updated",
        )

        # --------------------------------------------------
        # PI-HOLE
        # --------------------------------------------------

        self._collect(
            name="pihole",
            collector=pihole_collector.collect,
            now=now,
            interval=config.PIHOLE_INTERVAL,
            state_attribute="pihole",
            timestamp_attribute="pihole_updated",
        )

        # --------------------------------------------------
        # Stan cache
        # --------------------------------------------------

        self.state.last_update = now

        self.state.running = True

        self._initialized = True

        return self.state

    # ======================================================
    # FORCE REFRESH
    # ======================================================

    def force_refresh(
        self,
        name: str | None = None,
    ) -> None:
        """
        Wymusza ponowne pobranie danych.

        Przykłady:

            cache.force_refresh()

        wymusza odświeżenie wszystkiego.

            cache.force_refresh("pihole")

        wymusza tylko Pi-hole.
        """

        if name is None:

            self._last_update.clear()

            self._initialized = False

            return

        self._last_update.pop(
            name,
            None,
        )

    # ======================================================
    # STATUS
    # ======================================================

    def get_last_update(
        self,
        name: str,
    ) -> float:
        """
        Zwraca czas ostatniego odświeżenia
        konkretnego collectora.
        """

        return self._last_update.get(
            name,
            0.0,
        )

    # ------------------------------------------------------

    def get_age(
        self,
        name: str,
    ) -> float:
        """
        Zwraca wiek danych w sekundach.
        """

        last_update = self.get_last_update(
            name
        )

        if last_update == 0:
            return float("inf")

        return max(
            0.0,
            time.monotonic()
            - last_update,
        )


# ==========================================================
# GLOBALNA INSTANCJA
# ==========================================================

dashboard_cache = DashboardCache()