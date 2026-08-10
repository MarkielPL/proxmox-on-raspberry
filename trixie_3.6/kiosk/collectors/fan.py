"""
collectors/fan.py

Monitoring wentylatora PWM Raspberry Pi.

Aktualnie wykrywany układ:

/sys/class/hwmon/hwmon*/name
    -> pwmfan

fan1_input
    -> RPM

pwm1
    -> wartość PWM

pwm1_enable
    -> tryb PWM

Collector NIE steruje wentylatorem.
Tylko odczytuje jego stan.
"""

from __future__ import annotations

from pathlib import Path

import config

from models import FanInfo


class FanCollector:
    """
    Kolektor wentylatora PWM.
    """

    BASE_PATH = Path(
        "/sys/class/hwmon"
    )

    # ======================================================
    # FIND PWMFAN
    # ======================================================

    def _find_hwmon(self) -> Path | None:
        """
        Znajduje hwmon obsługujący pwmfan.
        """

        if not self.BASE_PATH.exists():
            return None

        for hwmon in sorted(
            self.BASE_PATH.glob(
                "hwmon*"
            )
        ):

            name_file = hwmon / "name"

            try:

                name = (
                    name_file.read_text(
                        encoding="utf-8"
                    ).strip()
                )

            except OSError:

                continue

            if name == "pwmfan":
                return hwmon

        return None

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
    # COLLECT
    # ======================================================

    def collect(self) -> FanInfo:
        """
        Pobiera stan wentylatora.
        """

        hwmon = self._find_hwmon()

        if hwmon is None:

            return FanInfo(
                available=False,
                status="not detected",
            )

        fan_path = (
            hwmon / "fan1_input"
        )

        pwm_path = (
            hwmon / "pwm1"
        )

        enable_path = (
            hwmon / "pwm1_enable"
        )

        rpm = self._read_int(
            fan_path
        )

        pwm = self._read_int(
            pwm_path
        )

        pwm_enabled = self._read_int(
            enable_path
        )

        # --------------------------------------------------
        # PWM 8-bit / 0-255
        # --------------------------------------------------

        pwm_percent = 0.0

        if config.PWM_MAX > 0:

            pwm_percent = (
                pwm
                / config.PWM_MAX
                * 100.0
            )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        if rpm <= 0:

            status = "stopped"

        elif rpm < config.FAN_MIN_RPM:

            status = "low"

        elif rpm >= config.FAN_WARNING_RPM:

            status = "high"

        else:

            status = "running"

        return FanInfo(
            available=True,
            device="pwmfan",
            hwmon_path=str(hwmon),
            rpm=rpm,
            pwm=pwm,
            pwm_percent=pwm_percent,
            pwm_enabled=pwm_enabled,
            status=status,
        )


fan_collector = FanCollector()