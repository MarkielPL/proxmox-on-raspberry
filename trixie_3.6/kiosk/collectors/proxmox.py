"""
Monitoring lokalnego Proxmox VE.

Architektura systemu:

    Debian Trixie
        │
        └── Proxmox VE 9
                │
                └── LXC CT100
                        │
                        └── Pi-hole

Collector korzysta wyłącznie z lokalnych
poleceń Proxmox:

    pveversion
    pct list
    pct status
    pct config

Nie wykonuje operacji modyfikujących system.
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
    Kolektor informacji o lokalnym Proxmox VE.
    """

    # ======================================================
    # EXECUTE COMMAND
    # ======================================================

    @staticmethod
    def _run(
        command: list[str],
        timeout: float = 2.0,
    ) -> str:
        """
        Bezpiecznie wykonuje lokalne polecenie.
        """

        try:

            result = subprocess.run(
                command,
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
    # VERSION
    # ======================================================

    def _get_version(
        self,
    ) -> str:
        """
        Odczytuje wersję pve-manager.
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

            if line.startswith(
                "pve-manager:"
            ):

                return line.split(
                    ":",
                    1,
                )[1].strip()

        return ""

    # ======================================================
    # NODE
    # ======================================================

    @staticmethod
    def _get_node() -> str:
        """
        Nazwa noda Proxmox.
        """

        return (
            config.PROXMOX_NODE
            or socket.gethostname()
        )

    # ======================================================
    # CONTAINER STATUS
    # ======================================================

    def _get_container_status(
        self,
        vmid: int,
    ) -> str:
        """
        Pobiera status kontenera.
        """

        output = self._run(
            [
                "pct",
                "status",
                str(vmid),
            ]
        )

        output = output.lower()

        if "running" in output:
            return "running"

        if "stopped" in output:
            return "stopped"

        return "unknown"

    # ======================================================
    # CONTAINER CONFIG
    # ======================================================

    def _get_container_name(
        self,
        vmid: int,
    ) -> str:
        """
        Pobiera hostname kontenera.
        """

        output = self._run(
            [
                "pct",
                "config",
                str(vmid),
            ]
        )

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
        """
        Pobiera podstawowe informacje o LXC.
        """

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
    # ALL CONTAINERS
    # ======================================================

    def _get_containers(
        self,
    ) -> list[
        ProxmoxContainerInfo
    ]:
        """
        Pobiera listę wszystkich LXC.

        pct list ma postać tabelaryczną:

            VMID Status Name
        """

        output = self._run(
            [
                "pct",
                "list",
            ]
        )

        if not output:
            return []

        containers = []

        lines = output.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if line.lower().startswith(
                "vmid"
            ):
                continue

            parts = line.split()

            if len(parts) < 3:
                continue

            try:

                vmid = int(
                    parts[0]
                )

            except ValueError:

                continue

            status = (
                parts[1].lower()
            )

            name = " ".join(
                parts[2:]
            )

            containers.append(
                ProxmoxContainerInfo(
                    vmid=vmid,
                    name=name,
                    status=status,
                )
            )

        return containers

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> ProxmoxInfo:
        """
        Pobiera stan lokalnego Proxmox VE.
        """

        node = self._get_node()

        version = (
            self._get_version()
        )

        if not version:

            return ProxmoxInfo(
                available=False,
                node=node,
                status="unavailable",
            )

        containers = (
            self._get_containers()
        )

        pihole = None

        for container in containers:

            if (
                container.vmid
                == config.PIHOLE_CTID
            ):

                pihole = container
                break

        return ProxmoxInfo(
            available=True,
            status="running",
            node=node,
            version=version,
            containers=containers,
            pihole=pihole,
        )


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

proxmox_collector = ProxmoxCollector()