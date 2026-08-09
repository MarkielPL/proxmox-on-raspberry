"""
collectors/storage.py

Monitoring systemów plików i aktywności dyskowej.

Collector:
    - wykrywa zamontowane systemy plików,
    - pokazuje wykorzystanie przestrzeni,
    - pomija systemy określone w config.py,
    - mierzy aktywność I/O.

Nie zawiera kodu UI.
"""

from __future__ import annotations

import time

import psutil

import config

from models import DiskInfo


class StorageCollector:
    """
    Kolektor pamięci masowej.
    """

    def __init__(self) -> None:

        self._previous_io = (
            psutil.disk_io_counters()
        )

        self._previous_time = (
            time.monotonic()
        )

    # ======================================================
    # DISK USAGE
    # ======================================================

    def _collect_partitions(
        self,
    ) -> list[DiskInfo]:

        result = []

        for partition in psutil.disk_partitions(
            all=False
        ):

            filesystem = (
                partition.fstype
            )

            if (
                filesystem
                in config.IGNORED_FILESYSTEMS
            ):
                continue

            if (
                not config.SHOW_TMPFS
                and filesystem == "tmpfs"
            ):
                continue

            mountpoint = (
                partition.mountpoint
            )

            if (
                not config.SHOW_BOOT_PARTITION
                and mountpoint in (
                    "/boot",
                    "/boot/firmware",
                )
            ):
                continue

            try:

                usage = (
                    psutil.disk_usage(
                        mountpoint
                    )
                )

            except (
                PermissionError,
                OSError,
            ):

                continue

            result.append(
                DiskInfo(
                    mountpoint=mountpoint,
                    device=partition.device,
                    filesystem=filesystem,
                    total=usage.total,
                    used=usage.used,
                    free=usage.free,
                    percent=usage.percent,
                )
            )

        return result

    # ======================================================
    # DISK IO
    # ======================================================

    def _collect_io(
        self,
    ) -> tuple[
        float,
        float,
    ]:

        current = (
            psutil.disk_io_counters()
        )

        now = time.monotonic()

        elapsed = (
            now
            - self._previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        if (
            current is None
            or self._previous_io is None
        ):

            self._previous_io = current
            self._previous_time = now

            return (
                0.0,
                0.0,
            )

        read_speed = max(
            0,
            current.read_bytes
            - self._previous_io.read_bytes,
        ) / elapsed

        write_speed = max(
            0,
            current.write_bytes
            - self._previous_io.write_bytes,
        ) / elapsed

        self._previous_io = current
        self._previous_time = now

        return (
            read_speed,
            write_speed,
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> list[DiskInfo]:
        """
        Pobiera informacje o systemach plików.
        """

        disks = (
            self._collect_partitions()
        )

        read_speed, write_speed = (
            self._collect_io()
        )

        # Na tym etapie pokazujemy
        # globalną aktywność I/O.
        #
        # W przyszłości możemy rozbudować
        # collector do osobnych urządzeń.

        if disks:

            disks[0].read_speed = (
                read_speed
            )

            disks[0].write_speed = (
                write_speed
            )

        return disks


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

storage_collector = StorageCollector()