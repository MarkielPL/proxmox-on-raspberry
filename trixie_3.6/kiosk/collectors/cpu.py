"""
Odczyt informacji o procesorze.

Moduł odpowiada wyłącznie za pobieranie danych
dotyczących CPU.

Nie tworzy paneli Rich.
Nie wykonuje formatowania tekstu.
"""

from __future__ import annotations

import os
import platform

import psutil

from models import CPUInfo


class CPUCollector:
    """
    Kolektor informacji o procesorze.
    """

    def __init__(self) -> None:
        """
        Pierwszy odczyt psutil.cpu_percent()
        nie posiada jeszcze poprzedniego punktu
        odniesienia.

        Wykonujemy więc pomiar inicjalizacyjny.
        """

        psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> CPUInfo:
        """
        Pobiera komplet informacji o CPU.
        """

        info = CPUInfo()

        # --------------------------------------------------
        # Obciążenie całego CPU
        # --------------------------------------------------

        info.usage = psutil.cpu_percent(
            interval=None
        )

        # --------------------------------------------------
        # Obciążenie poszczególnych rdzeni
        # --------------------------------------------------

        info.per_core = psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

        # --------------------------------------------------
        # Liczba rdzeni
        # --------------------------------------------------

        info.core_count = (
            psutil.cpu_count(
                logical=True
            )
            or 0
        )

        info.physical_core_count = (
            psutil.cpu_count(
                logical=False
            )
            or 0
        )

        # --------------------------------------------------
        # Częstotliwość CPU
        # --------------------------------------------------

        frequency = psutil.cpu_freq()

        if frequency is not None:

            info.frequency_current = (
                frequency.current
            )

            info.frequency_min = (
                frequency.min
            )

            info.frequency_max = (
                frequency.max
            )

        # --------------------------------------------------
        # Load average
        # --------------------------------------------------

        try:

            (
                info.load_1m,
                info.load_5m,
                info.load_15m,
            ) = os.getloadavg()

        except OSError:

            pass

        # --------------------------------------------------
        # Architektura
        # --------------------------------------------------

        info.architecture = (
            platform.machine()
        )

        # --------------------------------------------------
        # Nazwa procesora
        # --------------------------------------------------

        info.processor_name = (
            self.processor_name()
        )

        # --------------------------------------------------
        # Governor
        # --------------------------------------------------

        info.governor = (
            self.cpu_governor()
        )

        # --------------------------------------------------
        # Statystyki CPU
        # --------------------------------------------------

        stats = psutil.cpu_stats()

        info.ctx_switches = (
            stats.ctx_switches
        )

        info.interrupts = (
            stats.interrupts
        )

        info.soft_interrupts = (
            stats.soft_interrupts
        )

        info.syscalls = (
            stats.syscalls
        )

        # --------------------------------------------------
        # Czasy CPU
        # --------------------------------------------------

        times = psutil.cpu_times()

        info.user_time = (
            times.user
        )

        info.system_time = (
            times.system
        )

        info.idle_time = (
            times.idle
        )

        return info

    # ======================================================
    # PROCESSOR
    # ======================================================

    @staticmethod
    def processor_name() -> str:
        """
        Zwraca nazwę procesora.

        Raspberry Pi nie zawsze udostępnia nazwę
        przez platform.processor(), dlatego dodatkowo
        sprawdzamy /proc/cpuinfo.
        """

        name = platform.processor()

        if name:
            return name

        try:

            with open(
                "/proc/cpuinfo",
                "r",
                encoding="utf-8",
            ) as cpuinfo:

                for line in cpuinfo:

                    if line.startswith(
                        "Model"
                    ):

                        return (
                            line.split(
                                ":",
                                1,
                            )[1].strip()
                        )

                    if line.startswith(
                        "model name"
                    ):

                        return (
                            line.split(
                                ":",
                                1,
                            )[1].strip()
                        )

        except OSError:

            pass

        return "Unknown"

    # ======================================================
    # GOVERNOR
    # ======================================================

    @staticmethod
    def cpu_governor() -> str:
        """
        Zwraca aktualny governor CPU.
        """

        path = (
            "/sys/devices/system/cpu/"
            "cpu0/cpufreq/scaling_governor"
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as governor:

                return governor.read().strip()

        except OSError:

            return "unknown"

    # ======================================================
    # FREQUENCY
    # ======================================================

    @staticmethod
    def cpu_min_frequency() -> float:
        """
        Minimalna częstotliwość CPU w MHz.
        """

        frequency = psutil.cpu_freq()

        if frequency is None:
            return 0.0

        return frequency.min

    # ------------------------------------------------------

    @staticmethod
    def cpu_max_frequency() -> float:
        """
        Maksymalna częstotliwość CPU w MHz.
        """

        frequency = psutil.cpu_freq()

        if frequency is None:
            return 0.0

        return frequency.max

    # ======================================================
    # CPU STATS
    # ======================================================

    @staticmethod
    def cpu_stats() -> dict[str, int]:
        """
        Statystyki procesora.

        Funkcja może zostać wykorzystana później
        przez panel diagnostyczny.
        """

        stats = psutil.cpu_stats()

        return {
            "ctx_switches": stats.ctx_switches,
            "interrupts": stats.interrupts,
            "soft_interrupts": stats.soft_interrupts,
            "syscalls": stats.syscalls,
        }

    # ======================================================
    # CPU TIMES
    # ======================================================

    @staticmethod
    def cpu_times() -> dict[str, float]:
        """
        Czasy CPU.

        Mogą zostać wykorzystane przez panel
        diagnostyczny lub statystyki historyczne.
        """

        times = psutil.cpu_times()

        return {
            "user": times.user,
            "system": times.system,
            "idle": times.idle,
        }

    # ======================================================
    # CORE COUNT
    # ======================================================

    @staticmethod
    def logical_cores() -> int:
        """
        Liczba logicznych rdzeni CPU.
        """

        return (
            psutil.cpu_count(
                logical=True
            )
            or 0
        )

    # ------------------------------------------------------

    @staticmethod
    def physical_cores() -> int:
        """
        Liczba fizycznych rdzeni CPU.
        """

        return (
            psutil.cpu_count(
                logical=False
            )
            or 0
        )

    # ======================================================
    # ARCHITECTURE
    # ======================================================

    @staticmethod
    def architecture() -> str:
        """
        Architektura systemu.
        """

        return platform.machine()


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


cpu_collector = CPUCollector()