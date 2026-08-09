"""
collectors/system.py

Monitoring ogólnego stanu systemu Debian Trixie.

Collector odpowiada za:
    - hostname,
    - kernel,
    - system operacyjny,
    - architekturę,
    - uptime,
    - czas uruchomienia,
    - liczbę procesów,
    - load average.

Nie zawiera logiki UI.
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
    def _get_operating_system() -> str:
        """
        Odczytuje nazwę systemu z /etc/os-release.
        """

        path = "/etc/os-release"

        values: dict[str, str] = {}

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                for line in file:

                    line = line.strip()

                    if not line or "=" not in line:
                        continue

                    key, value = (
                        line.split(
                            "=",
                            1,
                        )
                    )

                    values[key] = (
                        value.strip('"')
                    )

        except OSError:

            return platform.system()

        return (
            values.get("PRETTY_NAME")
            or values.get("NAME")
            or platform.system()
        )

    # ======================================================
    # UPTIME
    # ======================================================

    @staticmethod
    def _get_uptime() -> int:
        """
        Czas pracy systemu w sekundach.
        """

        try:

            boot_time = (
                psutil.boot_time()
            )

            return max(
                0,
                int(
                    time.time()
                    - boot_time
                ),
            )

        except OSError:

            return 0

    # ======================================================
    # PROCESS COUNT
    # ======================================================

    @staticmethod
    def _get_process_count() -> int:
        """
        Liczba procesów widocznych dla psutil.
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
    def _get_load() -> tuple[
        float,
        float,
        float,
    ]:
        """
        Pobiera load average.
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
        Pobiera komplet informacji o systemie.
        """

        info = SystemInfo()

        info.hostname = (
            platform.node()
        )

        info.kernel = (
            platform.release()
        )

        info.operating_system = (
            self._get_operating_system()
        )

        info.architecture = (
            platform.machine()
        )

        info.uptime = (
            self._get_uptime()
        )

        info.boot_time = (
            psutil.boot_time()
        )

        info.process_count = (
            self._get_process_count()
        )

        (
            info.load_1m,
            info.load_5m,
            info.load_15m,
        ) = self._get_load()

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

system_collector = SystemCollector()