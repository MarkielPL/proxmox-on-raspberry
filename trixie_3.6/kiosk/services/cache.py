"""
Cache danych dashboardu.

Warstwa cache przechowuje ostatni poprawny wynik
kolektorów i określa, czy dane wymagają ponownego
pobrania.

Dzięki temu cięższe operacje nie są wykonywane
przy każdym odświeżeniu ekranu.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar


T = TypeVar("T")


@dataclass
class CacheEntry(
    Generic[T]
):
    """
    Pojedynczy wpis cache.
    """

    value: T | None = None

    timestamp: float = 0.0

    error: str = ""

    update_count: int = 0


class DataCache:
    """
    Prosty cache TTL.

    Każdy wpis ma własny czas życia.
    """

    def __init__(self) -> None:

        self._entries: dict[
            str,
            CacheEntry,
        ] = {}

    # ======================================================
    # GET ENTRY
    # ======================================================

    def get_entry(
        self,
        key: str,
    ) -> CacheEntry | None:
        """
        Zwraca cały wpis cache.
        """

        return self._entries.get(
            key
        )

    # ======================================================
    # GET
    # ======================================================

    def get(
        self,
        key: str,
        default=None,
    ):
        """
        Zwraca ostatnią wartość.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if entry is None:
            return default

        if entry.value is None:
            return default

        return entry.value

    # ======================================================
    # SET
    # ======================================================

    def set(
        self,
        key: str,
        value,
    ) -> None:
        """
        Zapisuje wartość do cache.
        """

        now = time.monotonic()

        entry = (
            self._entries.get(
                key
            )
        )

        if entry is None:

            entry = CacheEntry()

            self._entries[key] = (
                entry
            )

        entry.value = value

        entry.timestamp = now

        entry.error = ""

        entry.update_count += 1

    # ======================================================
    # ERROR
    # ======================================================

    def set_error(
        self,
        key: str,
        error: str,
    ) -> None:
        """
        Zapisuje błąd kolektora.

        Ostatnia poprawna wartość pozostaje
        dostępna dla dashboardu.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if entry is None:

            entry = CacheEntry()

            self._entries[key] = (
                entry
            )

        entry.error = str(
            error
        )

    # ======================================================
    # AGE
    # ======================================================

    def age(
        self,
        key: str,
    ) -> float:
        """
        Wiek danych w sekundach.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if (
            entry is None
            or entry.timestamp <= 0
        ):

            return float("inf")

        return max(
            time.monotonic()
            - entry.timestamp,
            0.0,
        )

    # ======================================================
    # VALID
    # ======================================================

    def valid(
        self,
        key: str,
        ttl: float,
    ) -> bool:
        """
        Sprawdza, czy dane są nadal świeże.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if (
            entry is None
            or entry.value is None
        ):

            return False

        return (
            self.age(key)
            < ttl
        )

    # ======================================================
    # NEED UPDATE
    # ======================================================

    def needs_update(
        self,
        key: str,
        interval: float,
    ) -> bool:
        """
        Zwraca True, jeżeli dane powinny
        zostać ponownie pobrane.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if (
            entry is None
            or entry.value is None
        ):

            return True

        return (
            self.age(key)
            >= interval
        )

    # ======================================================
    # CLEAR
    # ======================================================

    def clear(
        self,
        key: str | None = None,
    ) -> None:
        """
        Czyści jeden wpis albo cały cache.
        """

        if key is None:

            self._entries.clear()

            return

        self._entries.pop(
            key,
            None,
        )

    # ======================================================
    # KEYS
    # ======================================================

    def keys(self) -> list[str]:
        """
        Lista kluczy cache.
        """

        return list(
            self._entries.keys()
        )


# ==========================================================
# GLOBALNY CACHE
# ==========================================================

cache = DataCache()