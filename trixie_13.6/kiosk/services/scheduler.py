"""
services/scheduler.py

Harmonogram pracy Raspberry Pi Kiosk Dashboard.

Scheduler nie zbiera danych bezpośrednio.

Jego zadaniem jest:

- kontrolowanie częstotliwości głównej pętli,
- zapewnienie stabilnego czasu odświeżania,
- ograniczenie obciążenia CPU,
- obsługa czasu wykonania cyklu.
"""

from __future__ import annotations

import time

import config


class DashboardScheduler:
    """
    Prosty scheduler głównej pętli dashboardu.
    """

    def __init__(
        self,
        interval: float | None = None,
    ) -> None:

        self.interval = (
            interval
            if interval is not None
            else config.LIVE_REFRESH
        )

        self._cycle_started = (
            time.monotonic()
        )

    # ======================================================
    # START CYKLU
    # ======================================================

    def start_cycle(self) -> None:
        """
        Rozpoczyna nowy cykl.
        """

        self._cycle_started = (
            time.monotonic()
        )

    # ======================================================
    # CZAS CYKLU
    # ======================================================

    def elapsed(self) -> float:
        """
        Zwraca czas trwania aktualnego cyklu.
        """

        return (
            time.monotonic()
            - self._cycle_started
        )

    # ======================================================
    # OCZEKIWANIE
    # ======================================================

    def wait(self) -> None:
        """
        Czeka do rozpoczęcia kolejnego cyklu.
        """

        elapsed = self.elapsed()

        remaining = (
            self.interval
            - elapsed
        )

        if remaining > 0:

            time.sleep(
                remaining
            )

    # ======================================================
    # ZMIANA INTERWAŁU
    # ======================================================

    def set_interval(
        self,
        interval: float,
    ) -> None:
        """
        Zmienia główny interwał.
        """

        if interval <= 0:

            raise ValueError(
                "Scheduler interval "
                "must be greater than 0"
            )

        self.interval = interval