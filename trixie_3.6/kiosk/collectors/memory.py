"""
collectors/memory.py

Odczyt informacji o pamięci RAM oraz SWAP.

Moduł odpowiada wyłącznie za pobieranie danych.
Nie zawiera logiki UI.
"""

from __future__ import annotations

import psutil

from models import MemoryInfo
from models import SwapInfo


class MemoryCollector:
    """
    Kolektor pamięci RAM oraz SWAP.
    """

    # ======================================================
    # MEMORY
    # ======================================================

    def collect_memory(self) -> MemoryInfo:
        """
        Pobiera informacje o RAM.
        """

        vm = psutil.virtual_memory()

        return MemoryInfo(
            total=vm.total,
            used=vm.used,
            available=vm.available,
            free=vm.free,
            percent=vm.percent,
            cached=getattr(
                vm,
                "cached",
                0,
            ),
            buffers=getattr(
                vm,
                "buffers",
                0,
            ),
        )

    # ======================================================
    # SWAP
    # ======================================================

    def collect_swap(self) -> SwapInfo:
        """
        Pobiera informacje o SWAP.
        """

        swap = psutil.swap_memory()

        return SwapInfo(
            total=swap.total,
            used=swap.used,
            free=swap.free,
            percent=swap.percent,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> tuple[
        MemoryInfo,
        SwapInfo,
    ]:
        """
        Pobiera komplet informacji
        o RAM i SWAP.
        """

        return (
            self.collect_memory(),
            self.collect_swap(),
        )


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

memory_collector = MemoryCollector()