"""
collectors/system.py

Informacje o systemie:

- hostname
- kernel
- architektura
- Debian
- uptime
- load average
"""

from __future__ import annotations

import os
import platform
import socket
from pathlib import Path

from models import SystemInfo


class SystemCollector:
    """Collector informacji systemowych."""

    def _read_os_release(
        self,
    ) -> tuple[str, str]:

        path = Path(
            "/etc/os-release"
        )

        values = {}

        try:

            for line in path.read_text().splitlines():

                if "=" not in line:
                    continue

                key, value = (
                    line.split(
                        "=",
                        1,
                    )
                )

                values[key] = (
                    value.strip('"')
                )

        except OSError:

            return "", ""

        return (
            values.get(
                "PRETTY_NAME",
                "",
            ),
            values.get(
                "VERSION",
                "",
            ),
        )

    def collect(
        self,
    ) -> SystemInfo:

        os_name, os_version = (
            self._read_os_release()
        )

        try:

            uptime = int(
                float(
                    Path(
                        "/proc/uptime"
                    )
                    .read_text()
                    .split()[0]
                )
            )

        except (
            OSError,
            ValueError,
            IndexError,
        ):

            uptime = 0

        try:

            load_1m, load_5m, load_15m = (
                os.getloadavg()
            )

        except OSError:

            load_1m = 0.0
            load_5m = 0.0
            load_15m = 0.0

        return SystemInfo(
            hostname=socket.gethostname(),
            architecture=platform.machine(),
            kernel=platform.release(),
            os_name=os_name,
            os_version=os_version,
            uptime=uptime,
            load_1m=load_1m,
            load_5m=load_5m,
            load_15m=load_15m,
        )


system_collector = SystemCollector()