"""
collectors/nvme.py

Monitoring dysku NVMe Raspberry Pi.

Źródła:
    /sys/class/nvme
    /sys/class/hwmon

Collector nie wykonuje żadnych operacji zapisu.
"""

from __future__ import annotations

from pathlib import Path

from models import NvmeInfo


class NvmeCollector:
    """
    Collector NVMe.
    """

    BASE_PATH = Path(
        "/sys/class/nvme"
    )

    # ======================================================
    # READ TEXT
    # ======================================================

    @staticmethod
    def _read_text(
        path: Path,
    ) -> str:

        try:

            return (
                path.read_text(
                    encoding="utf-8"
                ).strip()
            )

        except OSError:

            return ""

    # ======================================================
    # READ INT
    # ======================================================

    @staticmethod
    def _read_int(
        path: Path,
    ) -> int:

        try:

            return int(
                path.read_text(
                    encoding="utf-8"
                ).strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0

    # ======================================================
    # FIND DEVICE
    # ======================================================

    def _find_device(
        self,
    ) -> Path | None:

        if not self.BASE_PATH.exists():
            return None

        for device in sorted(
            self.BASE_PATH.glob(
                "nvme*"
            )
        ):

            if device.is_dir():
                return device

        return None

    # ======================================================
    # TEMPERATURE
    # ======================================================

    def _get_temperature(
        self,
        device: Path,
    ) -> float:

        hwmon_path = (
            device / "hwmon"
        )

        if not hwmon_path.exists():
            return 0.0

        for sensor_dir in hwmon_path.glob(
            "hwmon*"
        ):

            for temp_file in sensor_dir.glob(
                "temp*_input"
            ):

                raw = self._read_text(
                    temp_file
                )

                try:

                    return (
                        float(raw)
                        / 1000.0
                    )

                except ValueError:

                    continue

        return 0.0

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> NvmeInfo:
        """
        Pobiera informacje o pierwszym wykrytym NVMe.
        """

        device = self._find_device()

        if device is None:

            return NvmeInfo(
                available=False
            )

        info = NvmeInfo(
            available=True,
            device=device.name,
        )

        info.model = self._read_text(
            device / "model"
        )

        info.serial = self._read_text(
            device / "serial"
        )

        info.firmware = self._read_text(
            device / "firmware_rev"
        )

        info.temperature = (
            self._get_temperature(
                device
            )
        )

        # --------------------------------------------------
        # SMART / health
        #
        # Nie każdy kernel / sterownik
        # udostępnia wszystkie pola sysfs.
        # --------------------------------------------------

        info.percent_used = float(
            self._read_int(
                device / "smart_log" /
                "percentage_used"
            )
        )

        info.power_on_hours = (
            self._read_int(
                device / "smart_log" /
                "power_on_hours"
            )
        )

        info.power_cycles = (
            self._read_int(
                device / "smart_log" /
                "power_cycles"
            )
        )

        info.unsafe_shutdowns = (
            self._read_int(
                device / "smart_log" /
                "unsafe_shutdowns"
            )
        )

        info.media_errors = (
            self._read_int(
                device / "smart_log" /
                "media_errors"
            )
        )

        return info


nvme_collector = NvmeCollector()