"""
Odczyt informacji o systemie Linux.

Moduł pobiera:

- hostname,
- kernel,
- system operacyjny,
- architekturę,
- uptime,
- czas uruchomienia,
- liczbę procesów,
- load average.

Nie tworzy paneli Rich.
"""

from __future__ import annotations

import os
import platform
import time

import psutil

from models import SystemInfo


class SystemCollector:
    """
    Kolektor informacji o systemie.
    """

    # ======================================================
    # OPERATING SYSTEM
    # ======================================================

    @staticmethod
    def operating_system() -> str:
        """
        Odczytuje nazwę systemu z /etc/os-release.
        """

        path = "/etc/os-release"

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                for line in file:

                    if line.startswith(
                        "PRETTY_NAME="
                    ):

                        return (
                            line.split(
                                "=",
                                1,
                            )[1]
                            .strip()
                            .strip('"')
                        )

        except OSError:

            pass

        return platform.system()

    # ======================================================
    # UPTIME
    # ======================================================

    @staticmethod
    def uptime() -> int:
        """
        Zwraca uptime systemu w sekundach.
        """

        try:

            return int(
                time.time()
                - psutil.boot_time()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0

    # ======================================================
    # PROCESS COUNT
    # ======================================================

    @staticmethod
    def process_count() -> int:
        """
        Zwraca liczbę procesów.
        """

        try:

            return len(
                psutil.pids()
            )

        except OSError:

            return 0

    # ======================================================
    # LOAD
    # ======================================================

    @staticmethod
    def load_average() -> tuple[
        float,
        float,
        float,
    ]:
        """
        Zwraca load average.
        """

        try:

            return os.getloadavg()

        except OSError:

            return (
                0.0,
                0.0,
                0.0,
            )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> SystemInfo:
        """
        Pobiera komplet informacji systemowych.
        """

        info = SystemInfo()

        # --------------------------------------------------
        # Hostname
        # --------------------------------------------------

        info.hostname = (
            platform.node()
        )

        # --------------------------------------------------
        # Kernel
        # --------------------------------------------------

        info.kernel = (
            platform.release()
        )

        # --------------------------------------------------
        # OS
        # --------------------------------------------------

        info.operating_system = (
            self.operating_system()
        )

        # --------------------------------------------------
        # Architecture
        # --------------------------------------------------

        info.architecture = (
            platform.machine()
        )

        # --------------------------------------------------
        # Boot time
        # --------------------------------------------------

        info.boot_time = (
            psutil.boot_time()
        )

        # --------------------------------------------------
        # Uptime
        # --------------------------------------------------

        info.uptime = (
            self.uptime()
        )

        # --------------------------------------------------
        # Process count
        # --------------------------------------------------

        info.process_count = (
            self.process_count()
        )

        # --------------------------------------------------
        # Load average
        # --------------------------------------------------

        (
            info.load_1m,
            info.load_5m,
            info.load_15m,
        ) = self.load_average()

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


system_collector = SystemCollector()