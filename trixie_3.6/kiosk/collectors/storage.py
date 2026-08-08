"""
Odczyt informacji o systemach plików.

Moduł wykorzystuje psutil.disk_partitions()
oraz psutil.disk_usage().

Nie tworzy paneli Rich.
"""

from __future__ import annotations

import time

import psutil

from models import DiskInfo

import config


class StorageCollector:
    """
    Kolektor systemów plików i przestrzeni dyskowej.
    """

    def __init__(self) -> None:

        self.previous_io = (
            psutil.disk_io_counters()
        )

        self.previous_time = (
            time.monotonic()
        )

    # ======================================================
    # DISK IO
    # ======================================================

    def get_io_speed(
        self,
    ) -> tuple[float, float]:
        """
        Oblicza całkowitą prędkość:

            read  = bytes/s
            write = bytes/s
        """

        current = (
            psutil.disk_io_counters()
        )

        current_time = (
            time.monotonic()
        )

        if current is None:
            return (
                0.0,
                0.0,
            )

        elapsed = (
            current_time
            - self.previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        read_bytes = (
            current.read_bytes
            - self.previous_io.read_bytes
        )

        write_bytes = (
            current.write_bytes
            - self.previous_io.write_bytes
        )

        self.previous_io = current

        self.previous_time = (
            current_time
        )

        return (
            max(
                read_bytes / elapsed,
                0.0,
            ),
            max(
                write_bytes / elapsed,
                0.0,
            ),
        )

    # ======================================================
    # FILESYSTEM FILTER
    # ======================================================

    @staticmethod
    def is_ignored(
        filesystem: str,
    ) -> bool:
        """
        Sprawdza, czy system plików powinien
        zostać pominięty w dashboardzie.
        """

        return (
            filesystem
            in config.IGNORED_FILESYSTEMS
        )

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> list[DiskInfo]:
        """
        Pobiera informacje o wszystkich
        interesujących systemach plików.
        """

        disks: list[
            DiskInfo
        ] = []

        (
            read_speed,
            write_speed,
        ) = self.get_io_speed()

        partitions = (
            psutil.disk_partitions(
                all=False
            )
        )

        for partition in partitions:

            if self.is_ignored(
                partition.fstype
            ):
                continue

            # --------------------------------------------------
            # Opcjonalne pominięcie /boot
            # --------------------------------------------------

            if (
                not config.SHOW_BOOT_PARTITION
                and partition.mountpoint
                in {
                    "/boot",
                    "/boot/firmware",
                }
            ):
                continue

            try:

                usage = psutil.disk_usage(
                    partition.mountpoint
                )

            except (
                PermissionError,
                OSError,
            ):

                continue

            disks.append(
                DiskInfo(
                    mountpoint=(
                        partition.mountpoint
                    ),
                    device=(
                        partition.device
                    ),
                    filesystem=(
                        partition.fstype
                    ),
                    total=(
                        usage.total
                    ),
                    used=(
                        usage.used
                    ),
                    free=(
                        usage.free
                    ),
                    percent=(
                        usage.percent
                    ),
                    read_speed=(
                        read_speed
                    ),
                    write_speed=(
                        write_speed
                    ),
                )
            )

        return disks


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


storage_collector = StorageCollector()