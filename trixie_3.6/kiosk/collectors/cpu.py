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

from models import CpuInfo


class CpuCollector:
    """
    Kolektor informacji o procesorze.
    """

    def __init__(self) -> None:
        """
        Pierwszy odczyt psutil jest zawsze niepoprawny.
        Dzięki temu kolejne pomiary są już prawidłowe.
        """
        psutil.cpu_percent(interval=None, percpu=True)

    # -----------------------------------------------------

    def collect(self) -> CpuInfo:
        """
        Pobiera wszystkie informacje o CPU.
        """

        info = CpuInfo()

        info.usage_total = psutil.cpu_percent(interval=None)

        info.usage_per_core = psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

        frequency = psutil.cpu_freq()

        if frequency is not None:
            info.frequency = frequency.current

        try:
            load1, load5, load15 = os.getloadavg()

            info.load1 = load1
            info.load5 = load5
            info.load15 = load15

        except OSError:
            pass

        return info

    # -----------------------------------------------------

    @staticmethod
    def logical_cores() -> int:
        """
        Liczba logicznych rdzeni.
        """

        return psutil.cpu_count() or 0

    # -----------------------------------------------------

    @staticmethod
    def physical_cores() -> int:
        """
        Liczba fizycznych rdzeni.
        """

        return psutil.cpu_count(logical=False) or 0

    # -----------------------------------------------------

    @staticmethod
    def architecture() -> str:
        """
        Architektura CPU.
        """

        return platform.machine()

    # -----------------------------------------------------

    @staticmethod
    def processor_name() -> str:
        """
        Nazwa procesora.
        """

        name = platform.processor()

        if name:
            return name

        try:

            with open("/proc/cpuinfo", "r") as cpuinfo:

                for line in cpuinfo:

                    if line.startswith("Model"):

                        return line.split(":", 1)[1].strip()

        except OSError:
            pass

        return "Unknown"

    # -----------------------------------------------------

    @staticmethod
    def cpu_governor() -> str:
        """
        Aktualny governor CPU.
        """

        path = (
            "/sys/devices/system/cpu/"
            "cpu0/cpufreq/scaling_governor"
        )

        try:

            with open(path) as governor:

                return governor.read().strip()

        except OSError:

            return "unknown"

    # -----------------------------------------------------

    @staticmethod
    def cpu_min_frequency() -> float:

        freq = psutil.cpu_freq()

        if freq is None:
            return 0.0

        return freq.min

    # -----------------------------------------------------

    @staticmethod
    def cpu_max_frequency() -> float:

        freq = psutil.cpu_freq()

        if freq is None:
            return 0.0

        return freq.max

    # -----------------------------------------------------

    @staticmethod
    def cpu_stats() -> dict:
        """
        Statystyki procesora.

        Przydadzą się później w panelu diagnostycznym.
        """

        stats = psutil.cpu_stats()

        return {

            "ctx_switches": stats.ctx_switches,

            "interrupts": stats.interrupts,

            "soft_interrupts": stats.soft_interrupts,

            "syscalls": stats.syscalls,

        }

    # -----------------------------------------------------

    @staticmethod
    def cpu_times() -> dict:
        """
        Czasy CPU.

        Mogą zostać wykorzystane
        w panelu zaawansowanym.
        """

        t = psutil.cpu_times()

        return {

            "user": t.user,

            "system": t.system,

            "idle": t.idle,

        }


cpu_collector = CpuCollector()