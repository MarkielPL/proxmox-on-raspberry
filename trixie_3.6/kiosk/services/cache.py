"""
services/cache.py

Pamięć podręczna danych Raspberry Pi Kiosk Dashboard.

Cache przechowuje ostatnie poprawne wyniki collectorów
oraz kontroluje interwały ich aktualizacji.

Architektura:

    collectors
         ↓
       cache
         ↓
    collector_manager
         ↓
    DashboardState
         ↓
       panels
         ↓
     dashboard

Założenia:

    - ostatnia poprawna wartość pozostaje dostępna
      nawet po chwilowym błędzie collectora,

    - błąd nie usuwa poprzednich danych,

    - każdy collector może posiadać własny interwał,

    - UI może odświeżać się często bez wykonywania
      ciężkich operacji przy każdym odświeżeniu,

    - cache nie zawiera żadnego kodu Rich/UI.
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
    Pojedynczy wpis pamięci podręcznej.

    value:
        Ostatnia poprawnie pobrana wartość.

    updated:
        Czas monotoniczny ostatniej poprawnej aktualizacji.

    error:
        Ostatni błąd związany z tym źródłem.
    """

    value: Any = None

    updated: float = 0.0

    error: str = ""


# ==========================================================
# DATA CACHE
# ==========================================================

class DataCache:
    """
    Centralny cache danych collectorów.
    """

    def __init__(self) -> None:

        self._data: dict[
            str,
            CacheEntry,
        ] = {}

    # ======================================================
    # SET
    # ======================================================

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Zapisuje nową poprawną wartość.

        Poprawna aktualizacja:

            - aktualizuje value,
            - aktualizuje timestamp,
            - kasuje poprzedni błąd.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            entry = CacheEntry()

            self._data[key] = entry

        entry.value = value

        entry.updated = time.monotonic()

        # Poprawny odczyt kasuje
        # poprzedni błąd.

        entry.error = ""

    # ======================================================
    # GET
    # ======================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Zwraca ostatnią wartość.

        Jeżeli wartość nie istnieje,
        zwracany jest default.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            return default

        return entry.value

    # ======================================================
    # GET ENTRY
    # ======================================================

    def get_entry(
        self,
        key: str,
    ) -> CacheEntry | None:
        """
        Zwraca kompletny wpis cache.
        """

        return self._data.get(
            key
        )

    # ======================================================
    # UPDATED
    # ======================================================

    def updated(
        self,
        key: str,
    ) -> float:
        """
        Zwraca czas ostatniej poprawnej aktualizacji.

        Jeżeli dane nigdy nie zostały pobrane,
        zwracane jest 0.0.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            return 0.0

        return entry.updated

    # ======================================================
    # AGE
    # ======================================================

    def age(
        self,
        key: str,
    ) -> float:
        """
        Zwraca wiek danych w sekundach.

        Brak danych:

            inf
        """

        updated = self.updated(
            key
        )

        if updated <= 0:

            return float("inf")

        return max(
            0.0,
            time.monotonic() - updated,
        )

    # ======================================================
    # NEEDS UPDATE
    # ======================================================

    def needs_update(
        self,
        key: str,
        interval: float,
    ) -> bool:
        """
        Sprawdza, czy dane wymagają aktualizacji.

        Aktualizacja jest wymagana gdy:

            1. wpis nie istnieje,

            2. wartość nigdy nie została
               poprawnie pobrana,

            3. interwał jest równy lub mniejszy
               od zera,

            4. upłynął określony interwał.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            return True

        if entry.updated <= 0:

            return True

        if interval <= 0:

            return True

        return (
            time.monotonic()
            - entry.updated
            >= interval
        )

    # ======================================================
    # SET ERROR
    # ======================================================

    def set_error(
        self,
        key: str,
        error: str,
    ) -> None:
        """
        Zapisuje błąd collectora.

        Istniejąca poprawna wartość
        pozostaje zachowana.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            entry = CacheEntry()

            self._data[key] = entry

        entry.error = error

    # ======================================================
    # GET ERROR
    # ======================================================

    def get_error(
        self,
        key: str,
    ) -> str:
        """
        Zwraca ostatni błąd.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            return ""

        return entry.error

    # ======================================================
    # HAS DATA
    # ======================================================

    def has(
        self,
        key: str,
    ) -> bool:
        """
        Sprawdza, czy cache zawiera wartość.
        """

        entry = self._data.get(
            key
        )

        if entry is None:

            return False

        return entry.value is not None

    # ======================================================
    # IS STALE
    # ======================================================

    def is_stale(
        self,
        key: str,
        max_age: float,
    ) -> bool:
        """
        Sprawdza, czy dane są starsze
        niż dopuszczalny czas.

        Jest to przydatne dla UI.

        Przykład:

            cache.is_stale(
                "proxmox",
                30,
            )
        """

        return self.age(
            key
        ) > max_age

    # ==========================================================
    # INVALIDATE
    # ==========================================================
    
    def invalidate(
        self,
        key: str | None = None,
    ) -> None:
        """
        Wymusza ponowną aktualizację danych.
    
        W przeciwieństwie do clear():
    
            - nie usuwa wartości,
            - nie usuwa danych diagnostycznych,
            - zeruje timestamp aktualizacji.
    
        Dzięki temu collector przy następnym wywołaniu
        zostanie wykonany ponownie, ale ostatnia poprawna
        wartość pozostaje dostępna.
        """
    
        if key is None:
        
            for entry in self._data.values():
                entry.updated = 0.0
    
            return
    
        entry = self._data.get(
            key
        )
    
        if entry is not None:
        
            entry.updated = 0.0
    
    # ======================================================
    # CLEAR
    # ======================================================

    def clear(
        self,
        key: str | None = None,
    ) -> None:
        """
        Usuwa dane z cache.

        key=None:
            czyści cały cache.

        key="cpu":
            czyści tylko CPU.
        """

        if key is None:

            self._data.clear()

            return

        self._data.pop(
            key,
            None,
        )

    # ======================================================
    # KEYS
    # ======================================================

    def keys(self) -> list[str]:
        """
        Zwraca listę wszystkich kluczy.
        """

        return list(
            self._data.keys()
        )

    # ======================================================
    # SNAPSHOT
    # ======================================================

    def snapshot(self) -> dict[str, Any]:
        """
        Zwraca prosty snapshot danych cache.

        Przydatne podczas diagnostyki
        oraz testów.
        """

        return {
            key: entry.value
            for key, entry
            in self._data.items()
        }

    # ======================================================
    # STATUS
    # ======================================================

    def status(
        self,
    ) -> dict[str, dict]:
        """
        Zwraca informacje diagnostyczne
        dotyczące wszystkich wpisów.
        """

        result: dict[
            str,
            dict,
        ] = {}

        for key, entry in self._data.items():

            result[key] = {

                "has_data": (
                    entry.value
                    is not None
                ),

                "age": self.age(
                    key
                ),

                "updated": (
                    entry.updated
                ),

                "error": (
                    entry.error
                ),
            }

        return result


# ==========================================================
# GLOBAL CACHE
# ==========================================================

cache = DataCache()