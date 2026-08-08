"""
Monitoring Pi-hole działającego jako LXC.

Architektura:

    Debian Trixie
        │
        └── Proxmox VE
                │
                └── CT100
                        │
                        └── Pi-hole

Collector:

- sprawdza stan LXC,
- sprawdza pihole-FTL,
- pobiera adres IP kontenera,
- próbuje odczytać statystyki Pi-hole.

Brak dostępności API nie powoduje awarii dashboardu.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request

import config

from models import PiHoleInfo


class PiHoleCollector:
    """
    Kolektor informacji o Pi-hole.
    """

    # ======================================================
    # PCT EXEC
    # ======================================================

    @staticmethod
    def _pct_exec(
        command: list[str],
        timeout: float = 3.0,
    ) -> str:
        """
        Wykonuje polecenie wewnątrz CT100.
        """

        try:

            result = subprocess.run(
                [
                    "pct",
                    "exec",
                    str(
                        config.PIHOLE_CTID
                    ),
                    "--",
                    *command,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):

            return ""

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    # ======================================================
    # DNS STATUS
    # ======================================================

    def _get_dns_status(
        self,
    ) -> str:
        """
        Sprawdza stan pihole-FTL.
        """

        output = self._pct_exec(
            [
                "systemctl",
                "is-active",
                "pihole-FTL",
            ]
        )

        if not output:
            return "unknown"

        return output.lower()

    # ======================================================
    # CONTAINER IP
    # ======================================================

    def _get_container_ip(
        self,
    ) -> str:
        """
        Pobiera adres IPv4 CT100.

        pct exec hostname -I działa
        niezależnie od konkretnej konfiguracji
        interfejsu sieciowego.
        """

        output = self._pct_exec(
            [
                "hostname",
                "-I",
            ]
        )

        if not output:
            return ""

        addresses = (
            output.split()
        )

        for address in addresses:

            if "." in address:
                return address

        return ""

    # ======================================================
    # API
    # ======================================================

    @staticmethod
    def _get_api_data(
        ip_address: str,
    ) -> dict:
        """
        Próbuje pobrać dane API Pi-hole.

        API jest wykonywane z hosta do adresu
        IP kontenera LXC.
        """

        if not ip_address:
            return {}

        urls = (
            f"http://{ip_address}/api/stats/summary",
            f"http://{ip_address}/api/stats/summary?sid=local",
        )

        for url in urls:

            try:

                request = (
                    urllib.request.Request(
                        url,
                        headers={
                            "User-Agent":
                                "Raspberry-Pi-Kiosk"
                        },
                    )
                )

                with urllib.request.urlopen(
                    request,
                    timeout=2,
                ) as response:

                    raw = response.read()

                    data = json.loads(
                        raw
                    )

                    if isinstance(
                        data,
                        dict,
                    ):

                        return data

            except (
                OSError,
                ValueError,
                urllib.error.URLError,
            ):

                continue

        return {}

    # ======================================================
    # SAFE NUMBER
    # ======================================================

    @staticmethod
    def _number(
        value,
        default=0,
    ):
        """
        Bezpieczna konwersja wartości API.
        """

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> PiHoleInfo:
        """
        Pobiera informacje o Pi-hole.
        """

        dns_status = (
            self._get_dns_status()
        )

        if dns_status == "unknown":

            return PiHoleInfo(
                available=False,
                status="unavailable",
                dns_status="unknown",
            )

        ip_address = (
            self._get_container_ip()
        )

        data = (
            self._get_api_data(
                ip_address
            )
        )

        info = PiHoleInfo(
            available=True,
            status="running",
            dns_status=dns_status,
        )

        # --------------------------------------------------
        # API
        # --------------------------------------------------

        if not data:
            return info

        # --------------------------------------------------
        # API VERSION
        # --------------------------------------------------

        version = data.get(
            "version"
        )

        if version is not None:

            info.api_version = str(
                version
            )

        # --------------------------------------------------
        # QUERY STATISTICS
        # --------------------------------------------------

        info.queries_total = int(
            self._number(
                data.get(
                    "queries",
                    data.get(
                        "dns_queries",
                        0,
                    ),
                )
            )
        )

        info.queries_blocked = int(
            self._number(
                data.get(
                    "blocked",
                    data.get(
                        "queries_blocked",
                        0,
                    ),
                )
            )
        )

        # --------------------------------------------------
        # BLOCKED %
        # --------------------------------------------------

        if info.queries_total > 0:

            info.blocked_percentage = (
                info.queries_blocked
                / info.queries_total
                * 100.0
            )

        # --------------------------------------------------
        # DOMAINS
        # --------------------------------------------------

        info.domains = int(
            self._number(
                data.get(
                    "domains",
                    data.get(
                        "domains_being_blocked",
                        0,
                    ),
                )
            )
        )

        # --------------------------------------------------
        # CLIENTS
        # --------------------------------------------------

        info.clients = int(
            self._number(
                data.get(
                    "clients",
                    0,
                )
            )
        )

        # --------------------------------------------------
        # QPS
        # --------------------------------------------------

        info.queries_per_second = (
            self._number(
                data.get(
                    "queries_per_second",
                    0.0,
                )
            )
        )

        # --------------------------------------------------
        # RESPONSE TIME
        # --------------------------------------------------

        info.response_time = (
            self._number(
                data.get(
                    "response_time",
                    0.0,
                )
            )
        )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

pihole_collector = PiHoleCollector()