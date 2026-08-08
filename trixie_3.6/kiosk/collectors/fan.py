"""
collectors/fan.py

Monitoring wentylatora PWM Raspberry Pi.

Przykładowe źródło:

/sys/class/hwmon/hwmon3/
    name
    fan1_input
    pwm1
    pwm1_enable
"""

from __future__ import annotations

from pathlib import Path

import config

from models import FanInfo


class FanCollector:
    """Collector wentylatora."""

    def __init__(self) -> None:

        self.hwmon_path: Path | None = None

        self._find_hwmon()

    # ======================================================
    # FIND HWMON
    # ======================================================

    def _find_hwmon(self) -> None:

        if not config.HWMON_PATH.exists():
            return

        for hwmon in sorted(
            config.HWMON_PATH.glob("hwmon*")
        ):

            try:

                name = (
                    hwmon / "name"
                ).read_text().strip()

            except OSError:

                continue

            if name == "pwmfan":

                self.hwmon_path = hwmon
                return

    # ======================================================
    # READ
    # ======================================================

    def _read_int(
        self,
        filename: str,
    ) -> int:

        if self.hwmon_path is None:
            return 0

        try:

            return int(
                (
                    self.hwmon_path
                    / filename
                )
                .read_text()
                .strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return 0

    # ======================================================
    # STATUS
    # ======================================================

    def _get_status(
        self,
        rpm: int,
        pwm: int,
        enabled: int,
    ) -> str:

        if not enabled:
            return "disabled"

        if pwm > 0 and rpm <= 0:
            return "warning"

        if rpm >= config.FAN_WARNING_RPM:
            return "high"

        if rpm > 0:
            return "normal"

        return "idle"

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(
        self,
    ) -> FanInfo:

        if self.hwmon_path is None:

            self._find_hwmon()

        if self.hwmon_path is None:

            return FanInfo(
                available=False
            )

        rpm = self._read_int(
            "fan1_input"
        )

        pwm = self._read_int(
            "pwm1"
        )

        enabled = self._read_int(
            "pwm1_enable"
        )

        pwm_percent = (
            pwm
            / config.PWM_MAX
            * 100
        )

        status = self._get_status(
            rpm,
            pwm,
            enabled,
        )

        return FanInfo(
            available=True,
            rpm=rpm,
            pwm=pwm,
            pwm_percent=pwm_percent,
            pwm_enabled=bool(enabled),
            status=status,
        )


fan_collector = FanCollector()