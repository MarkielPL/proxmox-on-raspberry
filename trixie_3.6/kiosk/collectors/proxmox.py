"""
collectors/proxmox.py

Monitoring lokalnego Proxmox VE 9.

Architektura:

    Raspberry Pi 5
        |
        +-- Debian Trixie
              |
              +-- Proxmox VE 9
                    |
                    +-- LXC CT100
                          |
                          +-- Pi-hole

Collector korzysta z lokalnych poleceń:

    pveversion
    pct status
    pct config
    pct exec

Nie korzysta z API HTTP Proxmoxa.
"""

from __future__ import annotations

import socket
import subprocess

import config

from models import (
    ProxmoxContainerInfo,
    ProxmoxInfo,
)


class ProxmoxCollector:
    """
    Kolektor lokalnego Proxmox VE.
    """

    # ======================================================
    # RUN COMMAND
    # ======================================================

    @staticmethod
    def _run(
        command: list[str],
        timeout: float = 2.0,
    ) -> str:
        """
        Wykonuje lokalne polecenie.
        """

        try:

            result = subprocess.run(
                command,
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
    # VERSION
    # ======================================================

    def _get_version(self) -> str:
        """
        Pobiera wersję Proxmoxa.
        """

        output = self._run(
            [
                "pveversion",
                "--verbose",
            ]
        )

        if not output:
            return ""

        for line in output.splitlines():

            line = line.strip()

            if line.startswith(
                "pve-manager:"
            ):

                return line.split(
                    ":",
                    1,
                )[1].strip()

        return ""

    # ======================================================
    # NODE STATUS
    # ======================================================

    def _get_node_status(self) -> str:
        """
        Sprawdza stan usługi pvedaemon.
        """

        output = self._run(
            [
                "systemctl",
                "is-active",
                "pvedaemon",
            ]
        )

        if output:
            return output

        return "unknown"

    # ======================================================
    # CONTAINER STATUS
    # ======================================================

    def _get_container_status(
        self,
        vmid: int,
    ) -> str:

        output = self._run(
            [
                "pct",
                "status",
                str(vmid),
            ]
        )

        if not output:
            return "unknown"

        text = output.lower()

        if "running" in text:
            return "running"

        if "stopped" in text:
            return "stopped"

        return "unknown"

    # ======================================================
    # CONTAINER CONFIG
    # ======================================================

    def _get_container_name(
        self,
        vmid: int,
    ) -> str:

        output = self._run(
            [
                "pct",
                "config",
                str(vmid),
            ]
        )

        if not output:
            return f"CT{vmid}"

        for line in output.splitlines():

            if line.startswith(
                "hostname:"
            ):

                return line.split(
                    ":",
                    1,
                )[1].strip()

        return f"CT{vmid}"

    # ======================================================
    # CONTAINER
    # ======================================================

    def _get_container(
        self,
        vmid: int,
    ) -> ProxmoxContainerInfo:

        status = (
            self._get_container_status(
                vmid
            )
        )

        name = (
            self._get_container_name(
                vmid
            )
        )

        return ProxmoxContainerInfo(
            vmid=vmid,
            name=name,
            status=status,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> ProxmoxInfo:
        """
        Pobiera stan Proxmoxa i CT Pi-hole.
        """

        node = (
            config.PROXMOX_NODE
            or socket.gethostname()
        )

        version = (
            self._get_version()
        )

        # Brak pveversion oznacza,
        # że Proxmox nie jest dostępny.
        if not version:

            return ProxmoxInfo(
                available=False,
                status="unknown",
                node=node,
            )

        status = (
            self._get_node_status()
        )

        pihole = (
            self._get_container(
                config.PIHOLE_CTID
            )
        )

        return ProxmoxInfo(
            available=True,
            status=status,
            node=node,
            version=version,
            pihole=pihole,
        )


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

proxmox_collector = ProxmoxCollector()