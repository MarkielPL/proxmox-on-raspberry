"""
Monitoring dysku NVMe Raspberry Pi.

Źródła:

    /sys/class/nvme/
    /sys/class/hwmon/

Moduł odpowiada wyłącznie za odczyt danych.

Nie tworzy paneli Rich.
Nie wykonuje formatowania UI.
"""

from __future__ import annotations

from pathlib import Path

from models import NvmeInfo


class NvmeCollector:
    """
    Kolektor informacji o urządzeniu NVMe.
    """

    BASE_PATH = Path(
        "/sys/class/nvme"
    )

    # ======================================================
    # ODCZYT TEKSTU
    # ======================================================

    @staticmethod
    def _read_text(
        path: Path,
    ) -> str:
        """
        Bezpiecznie odczytuje plik tekstowy.
        """

        try:

            return (
                path.read_text(
                    encoding="utf-8"
                )
                .strip()
            )

        except OSError:

            return ""

    # ======================================================
    # ODCZYT LICZBY
    # ======================================================

    @staticmethod
    def _read_int(
        path: Path,
    ) -> int:
        """
        Bezpiecznie odczytuje liczbę całkowitą.
        """

        try:

            return int(
                path.read_text(
                    encoding="utf-8"
                )
                .strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0

    # ======================================================
    # ODCZYT FLOAT
    # ======================================================

    @staticmethod
    def _read_float(
        path: Path,
    ) -> float:
        """
        Bezpiecznie odczytuje liczbę zmiennoprzecinkową.
        """

        try:

            return float(
                path.read_text(
                    encoding="utf-8"
                )
                .strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0.0

    # ======================================================
    # ZNAJDŹ NVMe
    # ======================================================

    def _find_device(
        self,
    ) -> Path | None:
        """
        Znajduje pierwszy kontroler NVMe.

        Przykład:

            /sys/class/nvme/nvme0
        """

        if not self.BASE_PATH.exists():
            return None

        devices = sorted(
            self.BASE_PATH.glob(
                "nvme[0-9]*"
            )
        )

        for device in devices:

            if device.is_dir():
                return device

        return None

    # ======================================================
    # TEMPERATURA
    # ======================================================

    def _get_temperature(
        self,
        device: Path,
    ) -> float:
        """
        Próbuje znaleźć temperaturę NVMe
        przez powiązany katalog hwmon.
        """

        hwmon_path = (
            device / "hwmon"
        )

        if not hwmon_path.exists():
            return 0.0

        for hwmon in hwmon_path.glob(
            "hwmon*"
        ):

            for temp_file in sorted(
                hwmon.glob(
                    "temp*_input"
                )
            ):

                raw = self._read_float(
                    temp_file
                )

                if raw == 0:
                    continue

                # hwmon podaje temperaturę
                # najczęściej w milistopniach.
                if abs(raw) > 1000:
                    raw /= 1000.0

                return raw

        return 0.0

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> NvmeInfo:
        """
        Pobiera informacje o pierwszym
        znalezionym urządzeniu NVMe.
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

        # --------------------------------------------------
        # MODEL
        # --------------------------------------------------

        info.model = self._read_text(
            device / "model"
        )

        # --------------------------------------------------
        # SERIAL
        # --------------------------------------------------

        info.serial = self._read_text(
            device / "serial"
        )

        # --------------------------------------------------
        # FIRMWARE
        # --------------------------------------------------

        info.firmware = self._read_text(
            device / "firmware_rev"
        )

        # --------------------------------------------------
        # TEMPERATURA
        # --------------------------------------------------

        info.temperature = (
            self._get_temperature(
                device
            )
        )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

nvme_collector = NvmeCollector()