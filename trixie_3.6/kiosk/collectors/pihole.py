"""
collectors/pihole.py

Monitoring Pi-hole działającego jako LXC.

Architektura:

Proxmox
    └── CT100
        └── Pi-hole

Collector:
    1. sprawdza stan CT100,
    2. sprawdza usługę pihole-FTL,
    3. próbuje pobrać statystyki Pi-hole
       przez API dostępne wewnątrz kontenera.

Nie steruje Pi-hole.
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
    Collector Pi-hole LXC.
    """

    # ======================================================
    # PCT EXEC
    # ======================================================

    @staticmethod
    def _pct_exec(
        command: list[str],
        timeout: float = 3.0,
    ) -> str:

        try:

            result = subprocess.run(
                [
                    "pct",
                    "exec",
                    str(config.PIHOLE_CTID),
                    "--",
                    *command,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                return ""

            return result.stdout.strip()

        except (
            OSError,
            subprocess.SubprocessError,
        ):

            return ""

    # ======================================================
    # CONTAINER STATUS
    # ======================================================

    def _container_running(self) -> bool:

        output = self._pct_exec(
            [
                "systemctl",
                "is-system-running",
            ]
        )

        if output in (
            "running",
            "degraded",
        ):
            return True

        status = subprocess.run(
            [
                "pct",
                "status",
                str(config.PIHOLE_CTID),
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
        )

        return (
            status.returncode == 0
            and "running"
            in status.stdout.lower()
        )

    # ======================================================
    # DNS STATUS
    # ======================================================

    def _get_dns_status(self) -> str:

        output = self._pct_exec(
            [
                "systemctl",
                "is-active",
                "pihole-FTL",
            ]
        )

        if output:
            return output

        # --------------------------------------------------
        # Fallback dla instalacji,
        # w której nazwa usługi różni się.
        # --------------------------------------------------

        output = self._pct_exec(
            [
                "pihole-FTL",
                "status",
            ]
        )

        if output:
            return "running"

        return "unknown"

    # ======================================================
    # API
    # ======================================================

    def _get_api_data(self) -> dict:
        """
        Próbuje pobrać dane API Pi-hole.

        API jest wywoływane wewnątrz LXC.
        """

        urls = (
            "http://127.0.0.1/api/stats/summary",
            "http://127.0.0.1/api/stats/summary?sid=local",
        )

        # --------------------------------------------------
        # Próba wykonania curl wewnątrz kontenera.
        # --------------------------------------------------

        for url in urls:

            output = self._pct_exec(
                [
                    "curl",
                    "-fsS",
                    "--max-time",
                    "2",
                    url,
                ],
                timeout=3.0,
            )

            if not output:
                continue

            try:

                data = json.loads(
                    output
                )

                if isinstance(
                    data,
                    dict,
                ):

                    return data

            except ValueError:

                continue

        return {}

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> PiHoleInfo:
        """
        Pobiera stan Pi-hole.
        """

        info = PiHoleInfo()

        if not self._container_running():

            info.available = False
            info.status = "container stopped"

            return info

        info.available = True
        info.status = "running"

        info.dns_status = (
            self._get_dns_status()
        )

        data = self._get_api_data()

        if not data:
            return info

        # --------------------------------------------------
        # API Pi-hole może różnić się strukturą
        # zależnie od wersji.
        #
        # Odczytujemy tylko pola, które występują.
        # --------------------------------------------------

        info.api_version = str(
            data.get(
                "version",
                data.get(
                    "api_version",
                    "unknown",
                ),
            )
        )

        try:

            info.response_time = float(
                data.get(
                    "response_time",
                    0.0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.response_time = 0.0

        try:

            info.queries_total = int(
                data.get(
                    "queries",
                    data.get(
                        "queries_total",
                        0,
                    ),
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.queries_total = 0

        try:

            info.queries_blocked = int(
                data.get(
                    "blocked",
                    data.get(
                        "queries_blocked",
                        0,
                    ),
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.queries_blocked = 0

        try:

            info.blocked_percentage = float(
                data.get(
                    "blocked_percentage",
                    0.0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.blocked_percentage = 0.0

        try:

            info.domains = int(
                data.get(
                    "domains",
                    0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.domains = 0

        try:

            info.clients = int(
                data.get(
                    "clients",
                    0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.clients = 0

        try:

            info.queries_per_second = float(
                data.get(
                    "queries_per_second",
                    0.0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            info.queries_per_second = 0.0

        return info


pihole_collector = PiHoleCollector()