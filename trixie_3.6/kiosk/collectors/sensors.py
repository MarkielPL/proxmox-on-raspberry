"""
collectors/sensors.py

Obsługa czujników Raspberry Pi 5.

Obsługiwane urządzenia:

• cpu_thermal
• nvme
• rp1_adc
• rpi_volt
• pwmfan

Moduł automatycznie wyszukuje urządzenia hwmon
po nazwie zamiast po numerze hwmonX.
"""

from __future__ import annotations

from pathlib import Path

from models import FanInfo
from models import TemperatureInfo

from utils import pwm_to_percent
from utils import read_float
from utils import read_int
from utils import read_text


class SensorCollector:

    HWMON_ROOT = Path("/sys/class/hwmon")

    def __init__(self) -> None:

        self.devices = self._discover_hwmon()

    # -------------------------------------------------

    def _discover_hwmon(self) -> dict[str, Path]:
        """
        Odszukuje wszystkie urządzenia hwmon.

        Zwraca np.

        {
            "cpu_thermal": Path(...),
            "nvme": Path(...),
            "pwmfan": Path(...)
        }
        """

        devices: dict[str, Path] = {}

        if not self.HWMON_ROOT.exists():
            return devices

        for hwmon in self.HWMON_ROOT.glob("hwmon*"):

            name = read_text(hwmon / "name")

            if name:

                devices[name] = hwmon

        return devices

    # -------------------------------------------------

    def _temperature(self, device: str) -> float:
        """
        Odczyt temp1_input.

        Większość sterowników Linux udostępnia
        temperaturę właśnie pod tą nazwą.
        """

        hwmon = self.devices.get(device)

        if hwmon is None:
            return 0.0

        temp = read_float(
            hwmon / "temp1_input"
        )

        if temp > 1000:
            temp /= 1000

        return temp

    # -------------------------------------------------

    def collect_temperatures(self) -> TemperatureInfo:

        info = TemperatureInfo()

        info.cpu = self._temperature(
            "cpu_thermal"
        )

        info.nvme = self._temperature(
            "nvme"
        )

        info.rp1 = self._temperature(
            "rp1_adc"
        )

        return info

    # -------------------------------------------------

    def collect_fan(self) -> FanInfo:

        fan = FanInfo()

        hwmon = self.devices.get(
            "pwmfan"
        )

        if hwmon is None:
            return fan

        fan.available = True

        fan.device = "pwmfan"

        fan.rpm = read_int(
            hwmon / "fan1_input"
        )

        fan.pwm = read_int(
            hwmon / "pwm1"
        )

        fan.pwm_mode = read_int(
            hwmon / "pwm1_enable"
        )

        fan.pwm_percent = pwm_to_percent(
            fan.pwm
        )

        return fan

    # -------------------------------------------------

    def collect_voltage(self) -> float:
        """
        Odczyt napięcia.

        Sterownik rpi_volt może eksportować
        różne kanały napięć.

        Aktualnie odczytywany jest temp1_input
        jeśli istnieje.

        W przyszłości można łatwo rozbudować
        o in0_input, in1_input itd.
        """

        hwmon = self.devices.get(
            "rpi_volt"
        )

        if hwmon is None:
            return 0.0

        value = read_float(
            hwmon / "temp1_input"
        )

        if value > 1000:
            value /= 1000

        return value

    # -------------------------------------------------

    def collect(self) -> tuple[
        TemperatureInfo,
        FanInfo,
    ]:

        temperatures = self.collect_temperatures()

        temperatures.voltage = (
            self.collect_voltage()
        )

        fan = self.collect_fan()

        return (
            temperatures,
            fan,
        )


sensor_collector = SensorCollector()