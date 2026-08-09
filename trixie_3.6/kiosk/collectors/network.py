"""
collectors/network.py

Monitoring interfejsu sieciowego.

Collector odpowiada za:
    - wykrywanie aktywnego interfejsu,
    - adres IP,
    - bramę domyślną,
    - DNS,
    - prędkość RX/TX,
    - całkowity transfer,
    - status interfejsu,
    - ping do hosta testowego.

Nie zawiera logiki UI.
"""

from __future__ import annotations

import re
import socket
import subprocess
import time

import psutil

import config

from models import NetworkInfo


class NetworkCollector:
    """
    Kolektor informacji o sieci.
    """

    def __init__(self) -> None:
        self._previous_counters = (
            psutil.net_io_counters()
        )

        self._previous_time = (
            time.monotonic()
        )

    # ======================================================
    # INTERFACE
    # ======================================================

    @staticmethod
    def _get_interface() -> str:
        """
        Próbuje znaleźć aktywny interfejs sieciowy.
        """

        stats = psutil.net_if_stats()

        candidates = []

        for name, data in stats.items():

            if not data.isup:
                continue

            if name == "lo":
                continue

            candidates.append(name)

        if not candidates:
            return ""

        # Preferuj Ethernet.
        for name in candidates:

            if name.startswith("eth"):
                return name

        # Następnie Wi-Fi.
        for name in candidates:

            if name.startswith("wlan"):
                return name

        return candidates[0]

    # ======================================================
    # IP ADDRESS
    # ======================================================

    @staticmethod
    def _get_ip_address(
        interface: str,
    ) -> str:
        """
        Pobiera adres IPv4 interfejsu.
        """

        if not interface:
            return ""

        addresses = psutil.net_if_addrs().get(
            interface,
            [],
        )

        for address in addresses:

            if address.family == socket.AF_INET:

                return address.address

        return ""

    # ======================================================
    # DEFAULT GATEWAY
    # ======================================================

    @staticmethod
    def _get_gateway() -> str:
        """
        Pobiera bramę domyślną z systemu.
        """

        try:

            result = subprocess.run(
                [
                    "ip",
                    "route",
                    "show",
                    "default",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                return ""

            match = re.search(
                r"default via ([0-9.]+)",
                result.stdout,
            )

            if match:
                return match.group(1)

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            pass

        return ""

    # ======================================================
    # DNS
    # ======================================================

    @staticmethod
    def _get_dns_server() -> str:
        """
        Próbuje odczytać pierwszy serwer DNS.
        """

        path = "/etc/resolv.conf"

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                for line in file:

                    line = line.strip()

                    if not line.startswith(
                        "nameserver"
                    ):
                        continue

                    parts = line.split()

                    if len(parts) >= 2:
                        return parts[1]

        except OSError:
            pass

        return ""

    # ======================================================
    # LINK SPEED
    # ======================================================

    @staticmethod
    def _get_link_speed(
        interface: str,
    ) -> int:
        """
        Prędkość linku w Mb/s.
        """

        if not interface:
            return 0

        stats = psutil.net_if_stats().get(
            interface
        )

        if stats is None:
            return 0

        return int(
            stats.speed or 0
        )

    # ======================================================
    # PING
    # ======================================================

    @staticmethod
    def _ping() -> tuple[
        float,
        bool,
    ]:
        """
        Wykonuje test ping.

        Zwraca:

            (czas_ms, dostępność)
        """

        target = config.PING_TARGET

        start = time.monotonic()

        try:

            result = subprocess.run(
                [
                    "ping",
                    "-c",
                    "1",
                    "-W",
                    "1",
                    target,
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            elapsed = (
                time.monotonic() - start
            ) * 1000

            if result.returncode == 0:

                return (
                    elapsed,
                    True,
                )

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            pass

        return (
            0.0,
            False,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> NetworkInfo:
        """
        Pobiera komplet informacji o sieci.
        """

        info = NetworkInfo()

        # --------------------------------------------------
        # INTERFACE
        # --------------------------------------------------

        interface = (
            self._get_interface()
        )

        info.interface = interface

        info.ip_address = (
            self._get_ip_address(
                interface
            )
        )

        info.gateway = (
            self._get_gateway()
        )

        info.dns_server = (
            self._get_dns_server()
        )

        info.link_speed = (
            self._get_link_speed(
                interface
            )
        )

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        if interface:

            stats = (
                psutil.net_if_stats()
                .get(interface)
            )

            if stats is not None:
                info.is_up = stats.isup

        # --------------------------------------------------
        # TRANSFER
        # --------------------------------------------------

        current = (
            psutil.net_io_counters()
        )

        current_time = (
            time.monotonic()
        )

        elapsed = (
            current_time
            - self._previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        info.download_speed = (
            max(
                0,
                current.bytes_recv
                - self._previous_counters.bytes_recv,
            )
            / elapsed
        )

        info.upload_speed = (
            max(
                0,
                current.bytes_sent
                - self._previous_counters.bytes_sent,
            )
            / elapsed
        )

        info.total_download = (
            current.bytes_recv
        )

        info.total_upload = (
            current.bytes_sent
        )

        self._previous_counters = current
        self._previous_time = current_time

        # --------------------------------------------------
        # PING
        # --------------------------------------------------

        (
            info.ping_ms,
            info.internet_available,
        ) = self._ping()

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

network_collector = NetworkCollector()