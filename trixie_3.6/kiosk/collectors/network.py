"""
Odczyt informacji o sieci.

Moduł odpowiada wyłącznie za pobieranie danych
sieciowych.

Nie tworzy paneli Rich.
Nie wykonuje formatowania tekstu.

Monitorowane są:

- interfejs sieciowy,
- adres IPv4,
- gateway,
- DNS,
- RX,
- TX,
- prędkość pobierania,
- prędkość wysyłania,
- prędkość linku,
- stan interfejsu,
- ping,
- dostępność Internetu.
"""

from __future__ import annotations

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
        """
        Inicjalizacja punktu odniesienia dla pomiaru
        prędkości RX/TX.
        """

        self.previous_counters = (
            psutil.net_io_counters()
        )

        self.previous_time = (
            time.monotonic()
        )

    # ======================================================
    # INTERFACE
    # ======================================================

    @staticmethod
    def get_primary_interface() -> str:
        """
        Próbuje znaleźć główny interfejs sieciowy.

        Pomijamy loopback oraz interfejsy bez adresu IPv4.
        """

        interfaces = psutil.net_if_addrs()

        stats = psutil.net_if_stats()

        # Preferujemy interfejs będący UP.
        for interface, addresses in (
            interfaces.items()
        ):

            if interface == "lo":
                continue

            if interface not in stats:
                continue

            if not stats[
                interface
            ].isup:
                continue

            for address in addresses:

                if (
                    address.family
                    == socket.AF_INET
                ):

                    return interface

        # Fallback — dowolny interfejs
        # posiadający IPv4.
        for interface, addresses in (
            interfaces.items()
        ):

            if interface == "lo":
                continue

            for address in addresses:

                if (
                    address.family
                    == socket.AF_INET
                ):

                    return interface

        return ""

    # ======================================================
    # IP
    # ======================================================

    @staticmethod
    def get_ip_address(
        interface: str,
    ) -> str:
        """
        Zwraca adres IPv4 wskazanego interfejsu.
        """

        if not interface:
            return ""

        addresses = psutil.net_if_addrs().get(
            interface,
            [],
        )

        for address in addresses:

            if (
                address.family
                == socket.AF_INET
            ):

                return address.address

        return ""

    # ======================================================
    # LINK SPEED
    # ======================================================

    @staticmethod
    def get_link_speed(
        interface: str,
    ) -> int:
        """
        Zwraca prędkość linku w Mb/s.

        psutil może zwrócić 0, jeśli sterownik
        nie udostępnia informacji.
        """

        if not interface:
            return 0

        stats = psutil.net_if_stats().get(
            interface
        )

        if stats is None:
            return 0

        return max(
            int(stats.speed),
            0,
        )

    # ======================================================
    # INTERFACE STATE
    # ======================================================

    @staticmethod
    def is_interface_up(
        interface: str,
    ) -> bool:
        """
        Sprawdza, czy interfejs jest aktywny.
        """

        if not interface:
            return False

        stats = psutil.net_if_stats().get(
            interface
        )

        if stats is None:
            return False

        return bool(stats.isup)

    # ======================================================
    # DEFAULT GATEWAY
    # ======================================================

    @staticmethod
    def get_gateway() -> str:
        """
        Odczytuje domyślną bramę z /proc/net/route.

        Nie wymaga dodatkowych pakietów.
        """

        path = Path(
            "/proc/net/route"
        )

        try:

            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()

        except OSError:

            return ""

        for line in lines[1:]:

            parts = line.split()

            if len(parts) < 3:
                continue

            interface = parts[0]

            destination = parts[1]

            gateway = parts[2]

            # 00000000 = default route
            if destination != "00000000":
                continue

            try:

                value = int(
                    gateway,
                    16,
                )

                address = socket.inet_ntoa(
                    value.to_bytes(
                        4,
                        byteorder="little",
                    )
                )

                # Interface musi istnieć.
                if interface:
                    return address

            except (
                ValueError,
                OSError,
            ):

                continue

        return ""

    # ======================================================
    # DNS
    # ======================================================

    @staticmethod
    def get_dns_server() -> str:
        """
        Odczytuje pierwszy znaleziony serwer DNS
        z /etc/resolv.conf.

        Obsługuje również wpisy:

        nameserver 1.1.1.1
        nameserver 192.168.1.1
        """

        path = Path(
            "/etc/resolv.conf"
        )

        try:

            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()

        except OSError:

            return ""

        for line in lines:

            line = line.strip()

            if not line.startswith(
                "nameserver"
            ):
                continue

            parts = line.split()

            if len(parts) >= 2:

                return parts[1]

        return ""

    # ======================================================
    # SPEED
    # ======================================================

    def get_speed(
        self,
    ) -> tuple[float, float]:
        """
        Oblicza chwilową prędkość:

        download = bytes/s
        upload   = bytes/s
        """

        current = (
            psutil.net_io_counters()
        )

        current_time = (
            time.monotonic()
        )

        elapsed = (
            current_time
            - self.previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        download = (
            current.bytes_recv
            - self.previous_counters.bytes_recv
        ) / elapsed

        upload = (
            current.bytes_sent
            - self.previous_counters.bytes_sent
        ) / elapsed

        self.previous_counters = current

        self.previous_time = (
            current_time
        )

        # Teoretycznie różnica nie powinna być
        # ujemna, ale po zmianie interfejsu lub
        # restartach może się to zdarzyć.
        download = max(
            download,
            0.0,
        )

        upload = max(
            upload,
            0.0,
        )

        return (
            download,
            upload,
        )

    # ======================================================
    # PING
    # ======================================================

    @staticmethod
    def ping(
        target: str,
    ) -> tuple[float, bool]:
        """
        Wykonuje pojedynczy ping.

        Zwraca:

            (czas_ms, sukces)

        """

        if not target:
            return 0.0, False

        command = [
            "ping",
            "-c",
            "1",
            "-W",
            "1",
            target,
        ]

        start = time.monotonic()

        try:

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):

            return 0.0, False

        elapsed = (
            time.monotonic()
            - start
        )

        if result.returncode != 0:
            return 0.0, False

        # Preferujemy wartość podaną przez ping,
        # ponieważ pomiar obejmuje dokładnie RTT.
        match = re.search(
            r"time[=<]([0-9.]+)\s*ms",
            result.stdout,
        )

        if match:

            try:

                return (
                    float(match.group(1)),
                    True,
                )

            except ValueError:

                pass

        return (
            elapsed * 1000,
            True,
        )

    # ======================================================
    # TOTAL COUNTERS
    # ======================================================

    @staticmethod
    def get_total_counters() -> tuple[int, int]:
        """
        Zwraca całkowitą ilość odebranych
        i wysłanych bajtów.
        """

        counters = (
            psutil.net_io_counters()
        )

        return (
            counters.bytes_recv,
            counters.bytes_sent,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> NetworkInfo:
        """
        Pobiera komplet informacji sieciowych.
        """

        info = NetworkInfo()

        # --------------------------------------------------
        # Interfejs
        # --------------------------------------------------

        info.interface = (
            self.get_primary_interface()
        )

        # --------------------------------------------------
        # IP
        # --------------------------------------------------

        info.ip_address = (
            self.get_ip_address(
                info.interface
            )
        )

        # --------------------------------------------------
        # Gateway
        # --------------------------------------------------

        info.gateway = (
            self.get_gateway()
        )

        # --------------------------------------------------
        # DNS
        # --------------------------------------------------

        info.dns_server = (
            self.get_dns_server()
        )

        # --------------------------------------------------
        # Interface state
        # --------------------------------------------------

        info.is_up = (
            self.is_interface_up(
                info.interface
            )
        )

        # --------------------------------------------------
        # Link speed
        # --------------------------------------------------

        info.link_speed = (
            self.get_link_speed(
                info.interface
            )
        )

        # --------------------------------------------------
        # RX/TX speed
        # --------------------------------------------------

        (
            info.download_speed,
            info.upload_speed,
        ) = self.get_speed()

        # --------------------------------------------------
        # Total RX/TX
        # --------------------------------------------------

        (
            info.total_download,
            info.total_upload,
        ) = self.get_total_counters()

        # --------------------------------------------------
        # Internet connectivity
        # --------------------------------------------------

        (
            info.ping_ms,
            info.internet_available,
        ) = self.ping(
            config.PING_TARGET
        )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


network_collector = NetworkCollector()