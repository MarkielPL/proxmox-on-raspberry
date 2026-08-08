"""
collectors/nvme.py

Monitoring dysku NVMe.

Źródła:

/sys/class/nvme/nvme*/
"""

from __future__ import annotations

from pathlib import Path

import config

from models import NvmeInfo


class NvmeCollector:
    """Collector NVMe."""

    BASE_PATH = Path(
        "/sys/class/nvme"
    )

    def _read_text(
        self,
        path: Path,
    ) -> str:

        try:

            return (
                path.read_text()
                .strip()
            )

        except OSError:

            return ""

    def _read_int(
        self,
        path: Path,
    ) -> int:

        try:

            return int(
                path.read_text().strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0

    def _find_device(
        self,
    ) -> Path | None:

        if not self.BASE_PATH.exists():
            return None

        devices = sorted(
            self.BASE_PATH.glob(
                "nvme*"
            )
        )

        for device in devices:

            if device.is_dir():
                return device

        return None

    def collect(
        self,
    ) -> NvmeInfo:

        device = self._find_device()

        if device is None:

            return NvmeInfo(
                available=False
            )

        model = self._read_text(
            device / "model"
        )

        temperature = 0.0

        # Próba odczytu przez hwmon.
        hwmon = device / "hwmon"

        if hwmon.exists():

            for sensor_dir in hwmon.glob(
                "hwmon*"
            ):

                for temp_file in sensor_dir.glob(
                    "temp*_input"
                ):

                    try:

                        raw = float(
                            temp_file
                            .read_text()
                            .strip()
                        )

                        temperature = (
                            raw / 1000
                        )

                        break

                    except (
                        OSError,
                        ValueError,
                    ):

                        continue

                if temperature:
                    break

        return NvmeInfo(
            available=True,
            model=model,
            temperature=temperature,
        )


nvme_collector = NvmeCollector()