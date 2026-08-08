"""
collectors/proxmox.py

Monitoring lokalnego Proxmox VE.

Architektura:

Debian Trixie
    └── Proxmox VE 9
          └── LXC CT100
                └── Pi-hole

Collector korzysta z lokalnych poleceń:

pct list
pveversion
hostname
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
    """Collector Proxmox."""

    def _run(
        self,
        command: list[str],
        timeout: float = 2.0,
    ) -> str:

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

    def _get_version(
        self,
    ) -> str:

        output = self._run(
            [
                "pveversion",
                "--verbose",
            ]
        )

        if not output:
            return ""

        for line in output.splitlines():

            if line.startswith(
                "pve-manager:"
            ):

                return line.split(
                    ":",
                    1,
                )[1].strip()

        return ""

    # ======================================================
    # LXC
    # ======================================================

    def _get_container(
        self,
        vmid: int,
    ) -> ProxmoxContainerInfo:

        output = self._run(
            [
                "pct",
                "status",
                str(vmid),
            ]
        )

        status = "unknown"

        if output:

            if "running" in output.lower():
                status = "running"

            elif "stopped" in output.lower():
                status = "stopped"

        name = f"CT{vmid}"

        config_output = self._run(
            [
                "pct",
                "config",
                str(vmid),
            ]
        )

        for line in config_output.splitlines():

            if line.startswith("hostname:"):

                name = line.split(
                    ":",
                    1,
                )[1].strip()

                break

        return ProxmoxContainerInfo(
            vmid=vmid,
            name=name,
            status=status,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> ProxmoxInfo:

        hostname = (
            config.PROXMOX_NODE
            or socket.gethostname()
        )

        version = self._get_version()

        if not version:

            return ProxmoxInfo(
                available=False,
                node=hostname,
            )

        pihole = self._get_container(
            config.PIHOLE_CTID
        )

        return ProxmoxInfo(
            available=True,
            node=hostname,
            version=version,
            status="running",
            pihole=pihole,
        )


proxmox_collector = ProxmoxCollector()