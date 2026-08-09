"""
collectors/nvme.py

Monitoring dysku NVMe Raspberry Pi 5.

Źródła:

    /sys/class/nvme/
    /sys/class/nvme/nvmeX/
    /sys/class/hwmon/

Collector próbuje odczytać:
    - model,
    - numer seryjny,
    - firmware,
    - temperaturę,
    - procent zużycia,
    - power-on hours,
    - power cycles,
    - unsafe shutdowns,
    - media errors.

Brak któregoś z parametrów nie jest traktowany
jako błąd całego collectora.
"""

from __future__ import annotations

from pathlib import Path

import config

from models import NvmeInfo


class NvmeCollector:
    """
    Kolektor NVMe.
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
                path.read_text()
                .strip()
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
                path.read_text()
                .strip()
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
        """
        Znajduje pierwsze urządzenie nvmeX.
        """

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

    # ======================================================
    # TEMPERATURE
    # ======================================================

    def _get_temperature(
        self,
        device: Path,
    ) -> float:
        """
        Próbuje znaleźć temperaturę NVMe
        poprzez powiązany hwmon.
        """

        hwmon_path = (
            device / "hwmon"
        )

        if not hwmon_path.exists():
            return 0.0

        for sensor_dir in sorted(
            hwmon_path.glob(
                "hwmon*"
            )
        ):

            for temp_file in sorted(
                sensor_dir.glob(
                    "temp*_input"
                )
            ):

                try:

                    raw = float(
                        temp_file
                        .read_text()
                        .strip()
                    )

                    return raw / 1000.0

                except (
                    OSError,
                    ValueError,
                ):

                    continue

        return 0.0

    # ======================================================
    # SMART / SYSFS ATTRIBUTES
    # ======================================================

    def _read_optional_int(
        self,
        device: Path,
        names: tuple[str, ...],
    ) -> int:
        """
        Próbuje znaleźć wartość pod kilkoma możliwymi nazwami.
        """

        for name in names:

            path = device / name

            if not path.exists():
                continue

            value = self._read_int(path)

            if value:
                return value

        return 0

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> NvmeInfo:
        """
        Pobiera informacje o pierwszym urządzeniu NVMe.
        """

        device = (
            self._find_device()
        )

        if device is None:

            return NvmeInfo(
                available=False
            )

        info = NvmeInfo(
            available=True,
            device=device.name,
        )

        # --------------------------------------------------
        # IDENTYFIKACJA
        # --------------------------------------------------

        info.model = (
            self._read_text(
                device / "model"
            )
        )

        info.serial = (
            self._read_text(
                device / "serial"
            )
        )

        info.firmware = (
            self._read_text(
                device / "firmware_rev"
            )
        )

        # --------------------------------------------------
        # TEMPERATURA
        # --------------------------------------------------

        info.temperature = (
            self._get_temperature(
                device
            )
        )

        # --------------------------------------------------
        # DANE EKSPLOATACYJNE
        # --------------------------------------------------

        info.power_on_hours = (
            self._read_optional_int(
                device,
                (
                    "power_on_hours",
                    "power_on_hours_raw",
                ),
            )
        )

        info.power_cycles = (
            self._read_optional_int(
                device,
                (
                    "power_cycles",
                    "power_cycles_raw",
                ),
            )
        )

        info.unsafe_shutdowns = (
            self._read_optional_int(
                device,
                (
                    "unsafe_shutdowns",
                    "unsafe_shutdowns_raw",
                ),
            )
        )

        info.media_errors = (
            self._read_optional_int(
                device,
                (
                    "media_errors",
                    "media_errors_raw",
                ),
            )
        )

        # --------------------------------------------------
        # TEMPERATURA Z CONFIG
        # --------------------------------------------------
        #
        # Sam collector nie podejmuje decyzji
        # o kolorze ani stanie alarmowym.
        #
        # Progi znajdują się w config.py
        # i będą wykorzystane przez panels.py.
        # --------------------------------------------------

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

nvme_collector = NvmeCollector()