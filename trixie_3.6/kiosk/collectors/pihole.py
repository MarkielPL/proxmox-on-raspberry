"""
collectors/pihole.py

Monitoring Pi-hole działającego jako LXC CT100.

Collector nie zakłada bezpośredniego dostępu do API Pi-hole
z poziomu hosta. W pierwszej kolejności sprawdzany jest stan
kontenera przez Proxmox.

Statystyki Pi-hole mogą być pobierane przez jego API,
jeżeli API jest dostępne lokalnie.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request

import config

from models import PiHoleInfo


class PiHoleCollector:
    """Collector Pi-hole."""

    # ======================================================
    # LOCAL LXC EXEC
    # ======================================================

    def _pct_exec(
        self,
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
    # DNS STATUS
    # ======================================================

    def _get_dns_status(
        self,
    ) -> str:

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
    # PI-HOLE VERSION 6 API
    # ======================================================

    def _get_api_data(
        self,
    ) -> dict:

        urls = (
            "http://127.0.0.1/api/stats/summary",
            "http://127.0.0.1/api/stats/summary?sid=local",
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

                    data = json.loads(
                        response.read()
                    )

                    if isinstance(
                        data,
                        dict,
                    ):

                        return data

            except (
                OSError,
                ValueError,
            ):

                continue

        return {}

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> PiHoleInfo:

        dns_status = (
            self._get_dns_status()
        )

        if dns_status == "unknown":

            return PiHoleInfo(
                available=False,
                dns_status="unknown",
            )

        return PiHoleInfo(
            available=True,
            dns_status=dns_status,
        )


pihole_collector = PiHoleCollector()