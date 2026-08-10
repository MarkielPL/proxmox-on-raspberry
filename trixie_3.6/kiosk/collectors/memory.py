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
    # COLLECT
    # ======================================================

    @staticmethod
    def collect() -> MemoryInfo:
        """
        Pobiera komplet informacji o RAM i SWAP.
        """

        info = MemoryInfo()

        # --------------------------------------------------
        # RAM
        # --------------------------------------------------

        memory = psutil.virtual_memory()

        info.total = memory.total
        info.used = memory.used
        info.available = memory.available
        info.free = memory.free
        info.percent = memory.percent

        info.cached = getattr(
            memory,
            "cached",
            0,
        )

        info.buffers = getattr(
            memory,
            "buffers",
            0,
        )

        # --------------------------------------------------
        # SWAP
        # --------------------------------------------------

        swap = psutil.swap_memory()

        info.swap_total = swap.total
        info.swap_used = swap.used
        info.swap_free = swap.free
        info.swap_percent = swap.percent

        return info


# ==========================================================
# GLOBAL COLLECTOR
# ==========================================================

memory_collector = MemoryCollector()