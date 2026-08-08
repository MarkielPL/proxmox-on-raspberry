"""
collectors/cpu.py

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


class CpuCollector:
    """
    Kolektor informacji o procesorze.
    """

    def __init__(self) -> None:
        """
        Inicjalizacja pomiarów CPU.

        Pierwszy pomiar psutil.cpu_percent()
        jest inicjalizacyjny.
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
        # UŻYCIE CPU
        # --------------------------------------------------

        per_core = psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

        info.per_core = per_core

        if per_core:

            info.usage = (
                sum(per_core)
                / len(per_core)
            )

        info.core_count = len(
            per_core
        )

        # --------------------------------------------------
        # LICZBA FIZYCZNYCH RDZENI
        # --------------------------------------------------

        info.physical_core_count = (
            psutil.cpu_count(
                logical=False
            )
            or 0
        )

        # --------------------------------------------------
        # CZĘSTOTLIWOŚĆ
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
        # LOAD AVERAGE
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
        # ARCHITEKTURA
        # --------------------------------------------------

        info.architecture = (
            platform.machine()
        )

        # --------------------------------------------------
        # NAZWA CPU
        # --------------------------------------------------

        info.processor_name = (
            self.processor_name()
        )

        # --------------------------------------------------
        # GOVERNOR
        # --------------------------------------------------

        info.governor = (
            self.cpu_governor()
        )

        # --------------------------------------------------
        # STATYSTYKI
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

        return info

    # ======================================================
    # PROCESSOR NAME
    # ======================================================

    @staticmethod
    def processor_name() -> str:
        """
        Odczytuje nazwę/model procesora.
        """

        name = (
            platform.processor()
        )

        if name:
            return name

        try:

            with open(
                "/proc/cpuinfo",
                "r",
                encoding="utf-8",
            ) as cpuinfo:

                for line in cpuinfo:

                    if (
                        line.startswith(
                            "Model"
                        )
                        or line.startswith(
                            "model name"
                        )
                    ):

                        return line.split(
                            ":",
                            1,
                        )[1].strip()

        except (
            OSError,
            IndexError,
        ):

            pass

        return "Unknown"

    # ======================================================
    # GOVERNOR
    # ======================================================

    @staticmethod
    def cpu_governor() -> str:
        """
        Aktualny governor CPU.
        """

        path = (
            "/sys/devices/system/cpu/"
            "cpu0/cpufreq/"
            "scaling_governor"
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
    # LOGICAL CORES
    # ======================================================

    @staticmethod
    def logical_cores() -> int:
        """
        Liczba logicznych rdzeni.
        """

        return (
            psutil.cpu_count()
            or 0
        )

    # ======================================================
    # PHYSICAL CORES
    # ======================================================

    @staticmethod
    def physical_cores() -> int:
        """
        Liczba fizycznych rdzeni.
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
        Architektura CPU.
        """

        return platform.machine()

    # ======================================================
    # FREQUENCY
    # ======================================================

    @staticmethod
    def cpu_min_frequency() -> float:
        """
        Minimalna częstotliwość CPU.
        """

        frequency = (
            psutil.cpu_freq()
        )

        if frequency is None:
            return 0.0

        return frequency.min

    @staticmethod
    def cpu_max_frequency() -> float:
        """
        Maksymalna częstotliwość CPU.
        """

        frequency = (
            psutil.cpu_freq()
        )

        if frequency is None:
            return 0.0

        return frequency.max

    # ======================================================
    # CPU STATS
    # ======================================================

    @staticmethod
    def cpu_stats() -> dict:
        """
        Statystyki CPU.
        """

        stats = psutil.cpu_stats()

        return {
            "ctx_switches":
                stats.ctx_switches,

            "interrupts":
                stats.interrupts,

            "soft_interrupts":
                stats.soft_interrupts,

            "syscalls":
                stats.syscalls,
        }

    # ======================================================
    # CPU TIMES
    # ======================================================

    @staticmethod
    def cpu_times() -> dict:
        """
        Czasy CPU.
        """

        times = psutil.cpu_times()

        return {
            "user": times.user,
            "system": times.system,
            "idle": times.idle,
        }


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

cpu_collector = CpuCollector()