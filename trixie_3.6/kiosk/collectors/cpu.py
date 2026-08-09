"""
collectors/cpu.py

Odczyt informacji o procesorze Raspberry Pi.

Collector odpowiada wyłącznie za pobieranie danych CPU.

Nie zawiera:
    - kodu Rich,
    - paneli,
    - formatowania UI,
    - logiki dashboardu.

Źródła danych:
    - psutil
    - /proc/cpuinfo
    - /sys/devices/system/cpu/
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

import psutil

from models import CPUInfo


# ==========================================================
# CPU COLLECTOR
# ==========================================================

class CpuCollector:
    """
    Kolektor informacji o procesorze.
    """

    GOVERNOR_PATH = Path(
        "/sys/devices/system/cpu/"
        "cpu0/cpufreq/scaling_governor"
    )

    # ------------------------------------------------------
    # INIT
    # ------------------------------------------------------

    def __init__(self) -> None:
        """
        Inicjalizacja collectora.

        Pierwszy pomiar psutil.cpu_percent()
        nie posiada jeszcze poprzedniego punktu
        odniesienia, dlatego wykonujemy go tutaj.
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
        Pobiera kompletny stan CPU.
        """

        info = CPUInfo()

        # --------------------------------------------------
        # Użycie CPU
        # --------------------------------------------------

        info.usage = psutil.cpu_percent(
            interval=None
        )

        info.per_core = psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

        # --------------------------------------------------
        # Liczba rdzeni
        # --------------------------------------------------

        info.core_count = (
            len(info.per_core)
        )

        # --------------------------------------------------
        # Częstotliwość
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

            load1, load5, load15 = (
                os.getloadavg()
            )

            info.load_1m = load1
            info.load_5m = load5
            info.load_15m = load15

        except OSError:

            pass

        return info

    # ======================================================
    # LOGICAL CORES
    # ======================================================

    @staticmethod
    def logical_cores() -> int:
        """
        Zwraca liczbę logicznych rdzeni CPU.
        """

        return (
            psutil.cpu_count(
                logical=True
            )
            or 0
        )

    # ======================================================
    # PHYSICAL CORES
    # ======================================================

    @staticmethod
    def physical_cores() -> int:
        """
        Zwraca liczbę fizycznych rdzeni CPU.
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
        Zwraca architekturę systemu.
        """

        return platform.machine()

    # ======================================================
    # PROCESSOR NAME
    # ======================================================

    @staticmethod
    def processor_name() -> str:
        """
        Próbuje ustalić nazwę procesora.

        Raspberry Pi nie zawsze zwraca nazwę
        przez platform.processor(), dlatego
        dodatkowo analizowany jest /proc/cpuinfo.
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

                    if line.lower().startswith(
                        "model"
                    ):

                        if ":" in line:

                            return (
                                line.split(
                                    ":",
                                    1,
                                )[1]
                                .strip()
                            )

        except OSError:

            pass

        return "Unknown"

    # ======================================================
    # CPU GOVERNOR
    # ======================================================

    @classmethod
    def cpu_governor(cls) -> str:
        """
        Zwraca aktualny governor CPU.

        Przykładowe wartości:

            performance
            powersave
            ondemand
            schedutil
        """

        try:

            return (
                cls.GOVERNOR_PATH
                .read_text(
                    encoding="utf-8"
                )
                .strip()
            )

        except OSError:

            return "unknown"

    # ======================================================
    # MIN FREQUENCY
    # ======================================================

    @staticmethod
    def cpu_min_frequency() -> float:
        """
        Zwraca minimalną częstotliwość CPU w MHz.
        """

        frequency = psutil.cpu_freq()

        if frequency is None:

            return 0.0

        return frequency.min

    # ======================================================
    # MAX FREQUENCY
    # ======================================================

    @staticmethod
    def cpu_max_frequency() -> float:
        """
        Zwraca maksymalną częstotliwość CPU w MHz.
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
        Zwraca statystyki CPU.

        Dane mogą zostać wykorzystane później
        przez panel diagnostyczny.
        """

        stats = psutil.cpu_stats()

        return {
            "ctx_switches": (
                stats.ctx_switches
            ),
            "interrupts": (
                stats.interrupts
            ),
            "soft_interrupts": (
                stats.soft_interrupts
            ),
            "syscalls": (
                stats.syscalls
            ),
        }

    # ======================================================
    # CPU TIMES
    # ======================================================

    @staticmethod
    def cpu_times() -> dict[str, float]:
        """
        Zwraca podstawowe czasy CPU.
        """

        times = psutil.cpu_times()

        return {
            "user": getattr(
                times,
                "user",
                0.0,
            ),
            "system": getattr(
                times,
                "system",
                0.0,
            ),
            "idle": getattr(
                times,
                "idle",
                0.0,
            ),
        }


# ==========================================================
# GLOBAL COLLECTOR
# ==========================================================

cpu_collector = CpuCollector()