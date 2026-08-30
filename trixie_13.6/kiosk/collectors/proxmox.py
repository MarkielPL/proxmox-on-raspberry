"""
collectors/proxmox.py

Monitoring lokalnego Proxmox VE.

Architektura:

Debian Trixie
    └── Proxmox VE 9
        └── LXC CT100
            └── Pi-hole

Collector korzysta z lokalnych narzędzi:
    pveversion
    pct
    pvesh

Nie korzysta z zewnętrznego API.
"""

from __future__ import annotations

import shutil
import socket
import subprocess

import config

from models import (
    ProxmoxContainerInfo,
    ProxmoxInfo,
)


class ProxmoxCollector:
    """
    Collector lokalnego Proxmox VE.
    """

    # ======================================================
    # COMMAND
    # ======================================================

    @staticmethod
    def _available(
        command: str,
    ) -> bool:

        return shutil.which(
            command
        ) is not None

    # ======================================================
    # RUN
    # ======================================================

    @staticmethod
    def _run(
        command: list[str],
        timeout: float = 3.0,
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

    def _get_version(self) -> str:

        if not self._available(
            "pveversion"
        ):
            return ""

        output = self._run(
            [
                "pveversion",
                "--verbose",
            ]
        )

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
    # CONTAINER STATUS
    # ======================================================

    def _get_container(
        self,
        vmid: int,
    ) -> ProxmoxContainerInfo:

        info = ProxmoxContainerInfo(
            vmid=vmid,
            name=f"CT{vmid}",
        )

        if not self._available("pct"):
            return info

        status_output = self._run(
            [
                "pct",
                "status",
                str(vmid),
            ]
        )

        status_lower = (
            status_output.lower()
        )

        if "running" in status_lower:

            info.status = "running"

        elif "stopped" in status_lower:

            info.status = "stopped"

        # --------------------------------------------------
        # Container config
        # --------------------------------------------------

        config_output = self._run(
            [
                "pct",
                "config",
                str(vmid),
            ]
        )

        for line in config_output.splitlines():

            if line.startswith(
                "hostname:"
            ):

                info.name = (
                    line.split(
                        ":",
                        1,
                    )[1].strip()
                )

                break

        # --------------------------------------------------
        # Runtime status
        # --------------------------------------------------

        if info.status == "running":

            runtime = self._run(
                [
                    "pvesh",
                    "get",
                    f"/nodes/"
                    f"{config.PROXMOX_NODE or socket.gethostname()}/"
                    f"lxc/{vmid}/status/current",
                    "--output-format",
                    "json",
                ]
            )

            if runtime:

                try:
                    import json

                    data = json.loads(
                        runtime
                    )

                    info.cpu = float(
                        data.get(
                            "cpu",
                            0.0,
                        )
                    )

                    info.memory = int(
                        data.get(
                            "mem",
                            0,
                        )
                    )

                    info.max_memory = int(
                        data.get(
                            "maxmem",
                            0,
                        )
                    )

                    info.swap = int(
                        data.get(
                            "swap",
                            0,
                        )
                    )

                    info.max_swap = int(
                        data.get(
                            "maxswap",
                            0,
                        )
                    )

                    info.uptime = int(
                        data.get(
                            "uptime",
                            0,
                        )
                    )

                    info.disk = int(
                        data.get(
                            "disk",
                            0,
                        )
                    )

                    info.max_disk = int(
                        data.get(
                            "maxdisk",
                            0,
                        )
                    )

                    info.network_in = int(
                        data.get(
                            "netin",
                            0,
                        )
                    )

                    info.network_out = int(
                        data.get(
                            "netout",
                            0,
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    pass

        return info

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> ProxmoxInfo:
        """
        Pobiera stan Proxmox oraz CT Pi-hole.
        """

        node = (
            config.PROXMOX_NODE
            or socket.gethostname()
        )

        version = self._get_version()

        if not version:

            return ProxmoxInfo(
                available=False,
                node=node,
                status="unavailable",
            )

        pihole = self._get_container(
            config.PIHOLE_CTID
        )

        return ProxmoxInfo(
            available=True,
            status="running",
            node=node,
            version=version,
            pihole=pihole,
        )


proxmox_collector = ProxmoxCollector()