"""
collectors/memory.py

Odczyt informacji o pamięci RAM oraz SWAP.

Źródło danych:
    psutil
"""

from __future__ import annotations

import psutil

from models import MemoryInfo


# ==========================================================
# MEMORY COLLECTOR
# ==========================================================

class MemoryCollector:
    """
    Kolektor RAM oraz SWAP.
    """

    # ======================================================
    # RAM
    # ======================================================

    @staticmethod
    def collect_memory() -> MemoryInfo:
        """
        Pobiera informacje o pamięci RAM.
        """

        vm = psutil.virtual_memory()

        info = MemoryInfo()

        info.total = vm.total
        info.used = vm.used
        info.available = vm.available
        info.free = vm.free
        info.percent = vm.percent

        # --------------------------------------------------
        # Linux
        # --------------------------------------------------

        info.cached = getattr(
            vm,
            "cached",
            0,
        )

        info.buffers = getattr(
            vm,
            "buffers",
            0,
        )

        return info

    # ======================================================
    # SWAP
    # ======================================================

    @staticmethod
    def collect_swap() -> dict[str, int | float]:
        """
        Pobiera informacje o SWAP.

        Zwracamy słownik, ponieważ obecny model
        DashboardState przechowuje dane SWAP
        bezpośrednio w MemoryInfo.
        """

        swap = psutil.swap_memory()

        return {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
        }

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> tuple[
        MemoryInfo,
        dict[str, int | float],
    ]:
        """
        Pobiera komplet informacji o RAM i SWAP.
        """

        memory = self.collect_memory()

        swap = self.collect_swap()

        return (
            memory,
            swap,
        )


# ==========================================================
# GLOBAL COLLECTOR
# ==========================================================

memory_collector = MemoryCollector()