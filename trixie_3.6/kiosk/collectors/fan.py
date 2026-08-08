"""
Odczyt informacji o wentylatorze PWM Raspberry Pi.

Moduł wykorzystuje interfejs Linux hwmon:

    fan*_input
    pwm*
    pwm*_enable

Nie steruje wentylatorem.

Jego zadaniem jest wyłącznie monitoring.
"""

from __future__ import annotations

from pathlib import Path

from models import FanInfo

import config


class FanCollector:
    """
    Kolektor informacji o wentylatorze PWM.
    """

    def __init__(self) -> None:

        self.hwmon_path = Path(
            config.HWMON_PATH
        )

    # ======================================================
    # READ INT
    # ======================================================

    @staticmethod
    def read_int(
        path: Path,
        default: int = 0,
    ) -> int:
        """
        Bezpieczny odczyt wartości całkowitej.
        """

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

            return default

    # ======================================================
    # FIND PWM FAN
    # ======================================================

    def find_pwmfan(self) -> Path | None:
        """
        Znajduje hwmon odpowiadający sterownikowi
        pwmfan.

        Preferowane jest dokładne dopasowanie:

            name == pwmfan
        """

        if not self.hwmon_path.exists():
            return None

        for hwmon in sorted(
            self.hwmon_path.glob(
                "hwmon*"
            )
        ):

            name_file = (
                hwmon / "name"
            )

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
    # PWM TO PERCENT
    # ======================================================

    @staticmethod
    def pwm_to_percent(
        pwm: int,
    ) -> float:
        """
        Przelicza wartość PWM na procent.

        Dla Twojego sterownika:

            pwm1 = 75

        przy:

            PWM_MAX = 255

        daje około:

            29.4%
        """

        if config.PWM_MAX <= 0:
            return 0.0

        percent = (
            pwm
            / config.PWM_MAX
            * 100.0
        )

        return max(
            0.0,
            min(
                percent,
                100.0,
            ),
        )

    # ======================================================
    # STATUS
    # ======================================================

    @staticmethod
    def get_status(
        rpm: int,
        pwm: int,
        pwm_enabled: int,
    ) -> str:
        """
        Określa logiczny stan wentylatora.

        Możliwe wartości:

            disabled
            stopped
            low
            normal
            warning
        """

        if pwm_enabled == 0:
            return "disabled"

        if rpm <= 0:
            return "stopped"

        if rpm < config.FAN_MIN_RPM:
            return "low"

        if rpm >= config.FAN_WARNING_RPM:
            return "warning"

        return "normal"

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> FanInfo:
        """
        Pobiera informacje o wentylatorze.
        """

        info = FanInfo()

        hwmon = self.find_pwmfan()

        if hwmon is None:

            return info

        info.available = True

        info.hwmon_path = str(
            hwmon
        )

        info.device = (
            "pwmfan"
        )

        # --------------------------------------------------
        # RPM
        # --------------------------------------------------

        fan_inputs = sorted(
            hwmon.glob(
                "fan*_input"
            )
        )

        if fan_inputs:

            info.rpm = self.read_int(
                fan_inputs[0]
            )

        # --------------------------------------------------
        # PWM
        # --------------------------------------------------

        pwm_files = sorted(
            hwmon.glob(
                "pwm[0-9]"
            )
        )

        if pwm_files:

            info.pwm = self.read_int(
                pwm_files[0]
            )

        # --------------------------------------------------
        # PWM ENABLE
        # --------------------------------------------------

        enable_files = sorted(
            hwmon.glob(
                "pwm[0-9]_enable"
            )
        )

        if enable_files:

            info.pwm_enabled = (
                self.read_int(
                    enable_files[0],
                    default=-1,
                )
            )

        # --------------------------------------------------
        # PWM %
        # --------------------------------------------------

        info.pwm_percent = (
            self.pwm_to_percent(
                info.pwm
            )
        )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        info.status = (
            self.get_status(
                info.rpm,
                info.pwm,
                info.pwm_enabled,
            )
        )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


fan_collector = FanCollector()