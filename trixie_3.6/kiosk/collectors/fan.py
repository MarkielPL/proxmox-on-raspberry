"""
collectors/fan.py

Monitoring wentylatora PWM Raspberry Pi.

Przykładowe źródło:

    /sys/class/hwmon/hwmon3/

    name
    fan1_input
    pwm1
    pwm1_enable

Collector nie steruje wentylatorem.
Tylko odczytuje jego aktualny stan.
"""

from __future__ import annotations

from pathlib import Path

import config

from models import FanInfo


class FanCollector:
    """
    Kolektor wentylatora PWM.
    """

    # ======================================================
    # FIND FAN
    # ======================================================

    def _find_fan(
        self,
    ) -> tuple[
        Path | None,
        Path | None,
        Path | None,
        Path | None,
    ]:
        """
        Wyszukuje pierwszy dostępny wentylator PWM.

        Zwraca:

            hwmon_path
            fan_input
            pwm
            pwm_enable
        """

        base = config.HWMON_PATH

        if not base.exists():
            return (
                None,
                None,
                None,
                None,
            )

        for hwmon in sorted(
            base.glob("hwmon*")
        ):

            name_file = (
                hwmon / "name"
            )

            try:

                name = (
                    name_file
                    .read_text()
                    .strip()
                )

            except OSError:

                name = ""

            # Preferujemy sterownik pwmfan.
            if name != "pwmfan":
                continue

            fan_files = sorted(
                hwmon.glob(
                    "fan*_input"
                )
            )

            pwm_files = sorted(
                hwmon.glob(
                    "pwm[0-9]"
                )
            )

            enable_files = sorted(
                hwmon.glob(
                    "pwm[0-9]_enable"
                )
            )

            fan_input = (
                fan_files[0]
                if fan_files
                else None
            )

            pwm = (
                pwm_files[0]
                if pwm_files
                else None
            )

            pwm_enable = (
                enable_files[0]
                if enable_files
                else None
            )

            return (
                hwmon,
                fan_input,
                pwm,
                pwm_enable,
            )

        return (
            None,
            None,
            None,
            None,
        )

    # ======================================================
    # READ INT
    # ======================================================

    @staticmethod
    def _read_int(
        path: Path | None,
    ) -> int:

        if path is None:
            return 0

        try:

            return int(
                path.read_text().strip()
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
        Pobiera aktualny stan wentylatora.
        """

        (
            hwmon_path,
            fan_input,
            pwm,
            pwm_enable,
        ) = self._find_fan()

        if hwmon_path is None:

            return FanInfo(
                available=False
            )

        rpm = self._read_int(
            fan_input
        )

        pwm_value = self._read_int(
            pwm
        )

        pwm_enabled = self._read_int(
            pwm_enable
        )

        pwm_percent = (
            pwm_value
            / config.PWM_MAX
            * 100
            if config.PWM_MAX > 0
            else 0.0
        )

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        if rpm < config.FAN_MIN_RPM:

            status = "low"

        elif rpm >= config.FAN_WARNING_RPM:

            status = "high"

        else:

            status = "normal"

        return FanInfo(
            available=True,
            device="pwmfan",
            hwmon_path=str(
                hwmon_path
            ),
            rpm=rpm,
            pwm=pwm_value,
            pwm_percent=pwm_percent,
            pwm_enabled=pwm_enabled,
            status=status,
        )


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

fan_collector = FanCollector()