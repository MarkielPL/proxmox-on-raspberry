"""
collectors/storage.py

Monitoring systemów plików i transferu dyskowego.

Collector zbiera:
    - punkty montowania,
    - urządzenia,
    - filesystem,
    - pojemność,
    - zajętość,
    - wolne miejsce,
    - chwilowy odczyt/zapis.

Nie zawiera UI.
"""

from __future__ import annotations

import time
from pathlib import Path

import psutil

import config
from models import DiskInfo


class StorageCollector:
    """
    Kolektor pamięci masowej.
    """

    def __init__(self) -> None:

        self._previous_time = time.monotonic()

        self._previous_read = 0
        self._previous_write = 0

        counters = psutil.disk_io_counters()

        if counters is not None:

            self._previous_read = (
                counters.read_bytes
            )

            self._previous_write = (
                counters.write_bytes
            )

    # ======================================================
    # DISK IO
    # ======================================================

    def _disk_speeds(
        self,
    ) -> tuple[float, float]:

        counters = psutil.disk_io_counters()

        now = time.monotonic()

        elapsed = (
            now - self._previous_time
        )

        if elapsed <= 0:
            elapsed = 1.0

        if counters is None:

            self._previous_time = now

            return 0.0, 0.0

        read_delta = max(
            0,
            counters.read_bytes
            - self._previous_read,
        )

        write_delta = max(
            0,
            counters.write_bytes
            - self._previous_write,
        )

        self._previous_read = (
            counters.read_bytes
        )

        self._previous_write = (
            counters.write_bytes
        )

        self._previous_time = now

        return (
            read_delta / elapsed,
            write_delta / elapsed,
        )

    # ======================================================
    # FILESYSTEM FILTER
    # ======================================================

    @staticmethod
    def _ignored_filesystem(
        filesystem: str,
    ) -> bool:

        if filesystem in (
            config.IGNORED_FILESYSTEMS
        ):
            return True

        return False

    # ======================================================
    # MOUNT FILTER
    # ======================================================

    @staticmethod
    def _ignored_mountpoint(
        mountpoint: str,
    ) -> bool:
        """
        Odfiltrowuje oczywiste wirtualne
        systemy montowania.
        """

        if mountpoint.startswith(
            "/proc"
        ):
            return True

        if mountpoint.startswith(
            "/sys"
        ):
            return True

        if mountpoint.startswith(
            "/dev"
        ):
            return True

        if mountpoint.startswith(
            "/run"
        ):
            return True

        return False

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> list[DiskInfo]:
        """
        Pobiera informacje o wszystkich
        interesujących systemach plików.
        """

        read_speed, write_speed = (
            self._disk_speeds()
        )

        result: list[DiskInfo] = []

        for partition in psutil.disk_partitions(
            all=False
        ):

            filesystem = (
                partition.fstype
            )

            mountpoint = (
                partition.mountpoint
            )

            if self._ignored_filesystem(
                filesystem
            ):
                continue

            if self._ignored_mountpoint(
                mountpoint
            ):
                continue

            if (
                not config.SHOW_TMPFS
                and filesystem == "tmpfs"
            ):
                continue

            if (
                not config.SHOW_BOOT_PARTITION
                and mountpoint in (
                    "/boot",
                    "/boot/firmware",
                )
            ):
                continue

            try:

                usage = psutil.disk_usage(
                    mountpoint
                )

            except (
                OSError,
                PermissionError,
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
                    read_speed=read_speed,
                    write_speed=write_speed,
                )
            )

        return result


storage_collector = StorageCollector()