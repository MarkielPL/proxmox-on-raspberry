"""
collectors/memory.py

Odczyt informacji o pamięci operacyjnej.

Moduł odpowiada wyłącznie za pobieranie
informacji o RAM i SWAP.
"""

from __future__ import annotations

import psutil

from models import MemoryInfo
from models import SwapInfo


class MemoryCollector:
    """
    Kolektor pamięci RAM oraz SWAP.
    """

    def collect_memory(self) -> MemoryInfo:
        """
        Pobiera informacje o pamięci RAM.
        """

        vm = psutil.virtual_memory()

        info = MemoryInfo()

        info.total = vm.total
        info.available = vm.available
        info.used = vm.used
        info.free = vm.free
        info.percent = vm.percent

        # Linux udostępnia te pola.
        # Dla zgodności z innymi systemami
        # sprawdzamy ich istnienie.

        info.cached = getattr(vm, "cached", 0)
        info.buffers = getattr(vm, "buffers", 0)

        return info

    # --------------------------------------------------

    def collect_swap(self) -> SwapInfo:
        """
        Pobiera informacje o SWAP.
        """

        swap = psutil.swap_memory()

        info = SwapInfo()

        info.total = swap.total
        info.used = swap.used
        info.free = swap.free
        info.percent = swap.percent

        return info

    # --------------------------------------------------

    def collect(self) -> tuple[MemoryInfo, SwapInfo]:
        """
        Pobiera komplet informacji o pamięci.
        """

        return (
            self.collect_memory(),
            self.collect_swap(),
        )


memory_collector = MemoryCollector()