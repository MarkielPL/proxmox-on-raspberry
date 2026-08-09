"""
collectors/pihole.py

Monitoring Pi-hole działającego jako:

    Debian Trixie
        |
        +-- Proxmox VE 9
              |
              +-- LXC CT100
                    |
                    +-- Pi-hole

Collector komunikuje się z kontenerem
przez lokalne:

    pct exec 100

Nie wymaga adresu IP Pi-hole.

Pobierane są:
    - stan kontenera,
    - stan pihole-FTL,
    - wersja Pi-hole,
    - podstawowe statystyki DNS,
    - liczba domen,
    - liczba klientów,
    - liczba zapytań.
"""

from __future__ import annotations

import json
import subprocess
import time

import config

from models import PiHoleInfo


class PiHoleCollector:
    """
    Kolektor Pi-hole.
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
        Wykonuje polecenie wewnątrz CT Pi-hole.
        """

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

    def _get_container_status(
        self,
    ) -> str:

        try:

            result = subprocess.run(
                [
                    "pct",
                    "status",
                    str(config.PIHOLE_CTID),
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                return "unknown"

            text = (
                result.stdout
                .strip()
                .lower()
            )

            if "running" in text:
                return "running"

            if "stopped" in text:
                return "stopped"

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            pass

        return "unknown"

    # ======================================================
    # FTL STATUS
    # ======================================================

    def _get_dns_status(self) -> str:
        """
        Stan pihole-FTL.
        """

        output = self._pct_exec(
            [
                "systemctl",
                "is-active",
                "pihole-FTL",
            ]
        )

        if output:
            return output

        return "unknown"

    # ======================================================
    # PI-HOLE VERSION
    # ======================================================

    def _get_version(self) -> str:
        """
        Pobiera wersję Pi-hole.
        """

        output = self._pct_exec(
            [
                "pihole",
                "-v",
            ]
        )

        if not output:
            return "unknown"

        # Szukamy pierwszej sensownej linii.
        for line in output.splitlines():

            line = line.strip()

            if "Pi-hole" in line:

                return line

            if "Core version" in line:

                return line

        return output.splitlines()[0]

    # ======================================================
    # API
    # ======================================================

    def _get_api_data(self) -> dict:
        """
        Próbuje pobrać dane z lokalnego API Pi-hole
        wewnątrz kontenera.

        W przypadku Pi-hole v6 najpierw próbujemy
        pihole-FTL przez dostępne polecenia lokalne.

        Funkcja jest odporna na brak konkretnego
        endpointu API.
        """

        # --------------------------------------------------
        # Próba użycia pihole-FTL --config
        # --------------------------------------------------

        output = self._pct_exec(
            [
                "pihole-FTL",
                "--config",
            ],
            timeout=3.0,
        )

        if output:

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
                pass

        return {}

    # ======================================================
    # DATABASE / STATS
    # ======================================================

    def _get_summary_from_cli(
        self,
    ) -> dict:
        """
        Próbuje uzyskać podstawowe informacje
        za pomocą lokalnych poleceń Pi-hole.

        Nie zakłada konkretnego API HTTP.
        """

        result: dict = {}

        # --------------------------------------------------
        # Liczba domen
        # --------------------------------------------------

        gravity = self._pct_exec(
            [
                "pihole",
                "-g",
                "-l",
            ],
            timeout=5.0,
        )

        if gravity:

            result["gravity"] = gravity

        return result

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> PiHoleInfo:
        """
        Pobiera stan Pi-hole.
        """

        info = PiHoleInfo()

        # --------------------------------------------------
        # STAN LXC
        # --------------------------------------------------

        container_status = (
            self._get_container_status()
        )

        if container_status != "running":

            info.available = False
            info.status = container_status
            info.dns_status = (
                "offline"
            )

            return info

        info.available = True
        info.status = "running"

        # --------------------------------------------------
        # FTL
        # --------------------------------------------------

        info.dns_status = (
            self._get_dns_status()
        )

        # --------------------------------------------------
        # VERSION
        # --------------------------------------------------

        info.api_version = (
            self._get_version()
        )

        # --------------------------------------------------
        # API / STATS
        # --------------------------------------------------

        start = time.monotonic()

        data = (
            self._get_api_data()
        )

        elapsed = (
            time.monotonic()
            - start
        )

        # Jeśli udało się uzyskać dane,
        # zapamiętujemy podstawowe wartości.
        #
        # Parser pozostaje celowo ostrożny,
        # ponieważ format danych zależy
        # od wersji Pi-hole.

        if data:

            info.queries_total = int(
                data.get(
                    "queries_total",
                    data.get(
                        "queries",
                        0,
                    ),
                )
                or 0
            )

            info.queries_blocked = int(
                data.get(
                    "queries_blocked",
                    data.get(
                        "blocked",
                        0,
                    ),
                )
                or 0
            )

            info.domains = int(
                data.get(
                    "domains",
                    data.get(
                        "domains_being_blocked",
                        0,
                    ),
                )
                or 0
            )

            info.clients = int(
                data.get(
                    "clients",
                    0,
                )
                or 0
            )

            if (
                info.queries_total > 0
                and info.queries_blocked >= 0
            ):

                info.blocked_percentage = (
                    info.queries_blocked
                    / info.queries_total
                    * 100
                )

        info.response_time = (
            elapsed * 1000
        )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

pihole_collector = PiHoleCollector()