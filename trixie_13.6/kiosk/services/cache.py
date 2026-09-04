"""
services/cache.py

Centralny cache danych dashboardu.

Odpowiada za:

- przechowywanie ostatniej poprawnej wartości,
- kontrolowanie interwałów aktualizacji,
- przechowywanie czasu ostatniej próby,
- przechowywanie czasu ostatniego sukcesu,
- przechowywanie błędów,
- zachowanie ostatnich poprawnych danych po błędzie.

WAŻNA ZASADA:

Częstotliwość odświeżania UI nie jest częstotliwością
pobierania danych.

UI może odświeżać się często, natomiast każdy collector
posiada własny interwał.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


# ==========================================================
# CACHE ENTRY
# ==========================================================


@dataclass
class CacheEntry:
    """
    Pojedynczy wpis cache.

    value:
        Ostatnia poprawna wartość.

    last_attempt:
        Czas ostatniej próby wykonania collectora.

    last_success:
        Czas ostatniego poprawnego wykonania.

    last_error:
        Ostatni komunikat błędu.

    error_at:
        Czas wystąpienia ostatniego błędu.
    """

    value: Any = None

    last_attempt: float | None = None
    last_success: float | None = None

    last_error: str | None = None
    error_at: float | None = None


# ==========================================================
# DATA CACHE
# ==========================================================


class DataCache:
    """
    Centralny cache danych collectorów.
    """

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    # ======================================================
    # INTERNAL
    # ======================================================

    def _get_entry(
        self,
        name: str,
    ) -> CacheEntry:
        """
        Pobiera istniejący wpis lub tworzy nowy.
        """

        if name not in self._entries:
            self._entries[name] = CacheEntry()

        return self._entries[name]

    # ======================================================
    # SHOULD UPDATE
    # ======================================================

    def needs_update(
        self,
        name: str,
        interval: float,
    ) -> bool:
        """
        Sprawdza, czy collector powinien zostać wykonany.

        Decyzja opiera się na czasie ostatniej próby,
        a nie wyłącznie na czasie ostatniego sukcesu.

        Dzięki temu chwilowy błąd API nie powoduje
        wielokrotnych prób w każdym cyklu UI.
        """

        if interval < 0:
            raise ValueError(
                "Cache interval cannot be negative."
            )

        entry = self._get_entry(name)

        if entry.last_attempt is None:
            return True

        elapsed = (
            time.monotonic()
            - entry.last_attempt
        )

        return elapsed >= interval

    # ======================================================
    # MARK ATTEMPT
    # ======================================================

    def mark_attempt(
        self,
        name: str,
        timestamp: float | None = None,
    ) -> None:
        """
        Rejestruje rozpoczęcie próby aktualizacji.
        """

        entry = self._get_entry(name)

        entry.last_attempt = (
            timestamp
            if timestamp is not None
            else time.monotonic()
        )

    # ======================================================
    # SET VALUE
    # ======================================================

    def set(
        self,
        name: str,
        value: Any,
        timestamp: float | None = None,
    ) -> None:
        """
        Zapisuje poprawną wartość.

        Ostatnia poprawna wartość zastępuje poprzednią.
        """

        now = (
            timestamp
            if timestamp is not None
            else time.monotonic()
        )

        entry = self._get_entry(name)

        entry.value = value
        entry.last_success = now
        entry.last_attempt = now

        # Poprawna aktualizacja kasuje poprzedni błąd.
        entry.last_error = None
        entry.error_at = None

    # ======================================================
    # GET VALUE
    # ======================================================

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Zwraca ostatnią poprawną wartość.
        """

        entry = self._entries.get(name)

        if entry is None:
            return default

        if entry.value is None:
            return default

        return entry.value

    # ======================================================
    # HAS VALUE
    # ======================================================

    def has(
        self,
        name: str,
    ) -> bool:
        """
        Sprawdza, czy cache posiada poprawną wartość.
        """

        entry = self._entries.get(name)

        return (
            entry is not None
            and entry.value is not None
        )

    # ======================================================
    # ERROR
    # ======================================================

    def set_error(
        self,
        name: str,
        error: str,
        timestamp: float | None = None,
    ) -> None:
        """
        Zapisuje błąd collectora.

        Ostatnia poprawna wartość pozostaje bez zmian.
        """

        now = (
            timestamp
            if timestamp is not None
            else time.monotonic()
        )

        entry = self._get_entry(name)

        entry.last_attempt = now
        entry.last_error = error
        entry.error_at = now

    # ======================================================
    # ENTRY
    # ======================================================

    def get_entry(
        self,
        name: str,
    ) -> CacheEntry | None:
        """
        Zwraca pełny wpis cache.

        Przydatne później dla UI i diagnostyki.
        """

        return self._entries.get(name)

    # ======================================================
    # LAST SUCCESS
    # ======================================================

    def last_success(
        self,
        name: str,
    ) -> float | None:
        """
        Zwraca timestamp ostatniego sukcesu.
        """

        entry = self._entries.get(name)

        if entry is None:
            return None

        return entry.last_success

    # ======================================================
    # LAST ERROR
    # ======================================================

    def last_error(
        self,
        name: str,
    ) -> str | None:
        """
        Zwraca ostatni błąd.
        """

        entry = self._entries.get(name)

        if entry is None:
            return None

        return entry.last_error

    # ======================================================
    # AGE
    # ======================================================

    def age(
        self,
        name: str,
    ) -> float | None:
        """
        Zwraca wiek ostatniej poprawnej wartości
        w sekundach.
        """

        success = self.last_success(name)

        if success is None:
            return None

        return max(
            0.0,
            time.monotonic() - success,
        )

    # ======================================================
    # CLEAR
    # ======================================================

    def clear(
        self,
        name: str | None = None,
    ) -> None:
        """
        Czyści cache.

        name=None:
            czyści cały cache.

        name="cpu":
            czyści tylko CPU.
        """

        if name is None:
            self._entries.clear()
            return

        self._entries.pop(
            name,
            None,
        )


# ==========================================================
# GLOBAL CACHE
# ==========================================================

cache = DataCache()