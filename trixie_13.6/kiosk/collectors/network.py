"""
collectors/network.py

Monitoring interfejsów sieciowych Raspberry Pi.

Collector zbiera:
    - aktywny interfejs,
    - adres IPv4,
    - bramę domyślną,
    - DNS,
    - status interfejsu,
    - prędkość linku,
    - transfer RX/TX,
    - chwilową prędkość pobierania/wysyłania,
    - ping do hosta testowego.

Nie zawiera logiki UI.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import time
from pathlib import Path

import psutil

import config
from models import NetworkInfo


class NetworkCollector:
    """
    Kolektor informacji o sieci.
    """

    def __init__(self) -> None:
        self._previous_time = time.monotonic()
        self._previous_recv = 0
        self._previous_sent = 0

        counters = psutil.net_io_counters()

        if counters is not None:
            self._previous_recv = counters.bytes_recv
            self._previous_sent = counters.bytes_sent

    # ======================================================
    # ACTIVE INTERFACE
    # ======================================================

    @staticmethod
    def _get_active_interface() -> str:
        """
        Próbuje znaleźć aktywny interfejs z adresem IPv4.
        """

        stats = psutil.net_if_stats()
        addresses = psutil.net_if_addrs()

        preferred = (
            "eth0",
            "end0",
            "enp1s0",
            "wlan0",
        )

        for interface in preferred:

            if interface not in stats:
                continue

            if not stats[interface].isup:
                continue

            for address in addresses.get(
                interface,
                [],
            ):

                if address.family == socket.AF_INET:
                    return interface

        for interface, status in stats.items():

            if not status.isup:
                continue

            if interface == "lo":
                continue

            for address in addresses.get(
                interface,
                [],
            ):

                if address.family == socket.AF_INET:
                    return interface

        return ""

    # ======================================================
    # IP ADDRESS
    # ======================================================

    @staticmethod
    def _get_ip_address(
        interface: str,
    ) -> str:
        """
        Zwraca IPv4 interfejsu.
        """

        if not interface:
            return ""

        for address in psutil.net_if_addrs().get(
            interface,
            [],
        ):

            if address.family == socket.AF_INET:
                return address.address

        return ""

    # ======================================================
    # DEFAULT GATEWAY
    # ======================================================

    @staticmethod
    def _get_gateway() -> str:
        """
        Pobiera domyślną bramę z tablicy routingu.
        """

        try:

            result = subprocess.run(
                [
                    "ip",
                    "-4",
                    "route",
                    "show",
                    "default",
                ],
                capture_output=True,
                text=True,
                timeout=1.5,
            )

            if result.returncode != 0:
                return ""

            match = re.search(
                r"default\s+via\s+(\S+)",
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
        Pobiera pierwszy skonfigurowany serwer DNS.

        Najpierw analizowany jest resolv.conf.
        """

        path = Path(
            "/etc/resolv.conf"
        )

        try:

            for line in path.read_text(
                encoding="utf-8"
            ).splitlines():

                line = line.strip()

                if line.startswith(
                    "nameserver "
                ):

                    return line.split(
                        None,
                        1,
                    )[1].strip()

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
        Zwraca prędkość linku w Mb/s.
        """

        if not interface:
            return 0

        stats = psutil.net_if_stats()

        interface_stats = stats.get(
            interface
        )

        if interface_stats is None:
            return 0

        speed = interface_stats.speed

        if speed is None or speed < 0:
            return 0

        return int(speed)

    # ======================================================
    # PING
    # ======================================================

    @staticmethod
    def _ping(
        target: str,
    ) -> tuple[float, bool]:
        """
        Wykonuje pojedynczy ping.

        Zwraca:
            (czas_ms, dostępność)
        """

        if not target:
            return 0.0, False

        try:

            start = time.monotonic()

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
                timeout=2.0,
            )

            elapsed = (
                time.monotonic() - start
            ) * 1000.0

            if result.returncode == 0:

                match = re.search(
                    r"time[=<]([\d.]+)",
                    result.stdout,
                )

                if match:
                    return (
                        float(match.group(1)),
                        True,
                    )

                return elapsed, True

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            pass

        return 0.0, False

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> NetworkInfo:
        """
        Pobiera kompletny stan sieci.
        """

        info = NetworkInfo()

        interface = (
            self._get_active_interface()
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
        # Status interfejsu
        # --------------------------------------------------

        interface_stats = (
            psutil.net_if_stats()
            .get(interface)
        )

        info.is_up = bool(
            interface_stats
            and interface_stats.isup
        )

        # --------------------------------------------------
        # Transfer
        # --------------------------------------------------

        counters = psutil.net_io_counters()

        now = time.monotonic()

        elapsed = (
            now - self._previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        if counters is not None:

            recv_delta = max(
                0,
                counters.bytes_recv
                - self._previous_recv,
            )

            sent_delta = max(
                0,
                counters.bytes_sent
                - self._previous_sent,
            )

            info.download_speed = (
                recv_delta / elapsed
            )

            info.upload_speed = (
                sent_delta / elapsed
            )

            info.total_download = (
                counters.bytes_recv
            )

            info.total_upload = (
                counters.bytes_sent
            )

            self._previous_recv = (
                counters.bytes_recv
            )

            self._previous_sent = (
                counters.bytes_sent
            )

        self._previous_time = now

        # --------------------------------------------------
        # Internet
        # --------------------------------------------------

        ping_ms, available = self._ping(
            config.PING_TARGET
        )

        info.ping_ms = ping_ms
        info.internet_available = available

        return info


network_collector = NetworkCollector()