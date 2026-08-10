"""
collectors/system.py

Monitoring ogólnego stanu systemu.

Zbiera:
    - hostname,
    - kernel,
    - system operacyjny,
    - architekturę,
    - uptime,
    - czas uruchomienia,
    - liczbę procesów,
    - load average.

System:
    Debian Trixie
    Raspberry Pi 5
"""

from __future__ import annotations

import os
import platform
import socket
import time
from pathlib import Path

import psutil

from models import SystemInfo


class SystemCollector:
    """
    Kolektor informacji systemowych.
    """

    # ======================================================
    # OS RELEASE
    # ======================================================

    @staticmethod
    def _get_os_name() -> str:
        """
        Odczytuje PRETTY_NAME z /etc/os-release.
        """

        path = Path(
            "/etc/os-release"
        )

        try:

            for line in path.read_text(
                encoding="utf-8"
            ).splitlines():

                if line.startswith(
                    "PRETTY_NAME="
                ):

                    value = line.split(
                        "=",
                        1,
                    )[1].strip()

                    return value.strip(
                        '"'
                    )

        except OSError:
            pass

        return platform.system()

    # ======================================================
    # UPTIME
    # ======================================================

    @staticmethod
    def _get_uptime() -> int:
        """
        Zwraca uptime w sekundach.
        """

        try:

            return int(
                time.time()
                - psutil.boot_time()
            )

        except OSError:

            return 0

    # ======================================================
    # PROCESS COUNT
    # ======================================================

    @staticmethod
    def _get_process_count() -> int:
        """
        Zwraca liczbę procesów.
        """

        try:

            return len(
                psutil.pids()
            )

        except (
            OSError,
            psutil.Error,
        ):

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
        Pobiera kompletny stan systemu.
        """

        info = SystemInfo()

        info.hostname = (
            socket.gethostname()
        )

        info.kernel = (
            platform.release()
        )

        info.operating_system = (
            self._get_os_name()
        )

        info.architecture = (
            platform.machine()
        )

        info.boot_time = (
            psutil.boot_time()
        )

        info.uptime = (
            self._get_uptime()
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


system_collector = SystemCollector()