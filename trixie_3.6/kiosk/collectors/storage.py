"""
collectors/storage.py

Monitoring systemów plików.
"""

from __future__ import annotations

import psutil

import config

from models import DiskInfo


class StorageCollector:
    """Collector dysków/systemów plików."""

    def collect(
        self,
    ) -> list[DiskInfo]:

        result = []

        try:

            partitions = (
                psutil.disk_partitions(
                    all=False
                )
            )

        except OSError:

            return result

        for partition in partitions:

            filesystem = (
                partition.fstype
            )

            if filesystem in (
                config.IGNORED_FILESYSTEMS
            ):
                continue

            if (
                not config.SHOW_BOOT_PARTITION
                and partition.mountpoint
                == "/boot/firmware"
            ):
                continue

            try:

                usage = (
                    psutil.disk_usage(
                        partition.mountpoint
                    )
                )

            except (
                OSError,
                PermissionError,
            ):

                continue

            result.append(
                DiskInfo(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    filesystem=filesystem,
                    total=usage.total,
                    used=usage.used,
                    free=usage.free,
                    percent=usage.percent,
                )
            )

        return result


storage_collector = StorageCollector()