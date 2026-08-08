"""
Odczyt informacji o pamięci operacyjnej.

Moduł odpowiada wyłącznie za pobieranie
informacji o RAM i SWAP.

Nie tworzy paneli Rich.
Nie wykonuje formatowania tekstu.
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
    # RAM
    # ======================================================

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

        # --------------------------------------------------
        # Linux udostępnia cached oraz buffers.
        #
        # getattr() zapewnia zgodność również wtedy,
        # gdy dane pole nie jest dostępne.
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

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> tuple[MemoryInfo, SwapInfo]:
        """
        Pobiera komplet informacji o pamięci:

        - RAM
        - SWAP
        """

        return (
            self.collect_memory(),
            self.collect_swap(),
        )


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


memory_collector = MemoryCollector()