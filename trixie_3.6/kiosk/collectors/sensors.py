"""
collectors/sensors.py

Monitoring temperatur Raspberry Pi 5.

Źródła:

    /sys/class/thermal
    /sys/class/hwmon

Collector wykrywa temperatury dostępne
w systemie Debian Trixie.
"""

from __future__ import annotations

from pathlib import Path

import psutil

import config

from models import TemperatureInfo
from models import TemperaturesInfo


class SensorCollector:
    """
    Kolektor temperatur i czujników.
    """

    # ======================================================
    # TEMPERATURE COLOR / NAME
    # ======================================================

    @staticmethod
    def _display_name(
        name: str,
        sensor: str,
    ) -> str:
        """
        Zamienia techniczną nazwę czujnika
        na nazwę przyjazną dla dashboardu.
        """

        mapping = config.TEMPERATURE_NAMES

        if sensor in mapping:
            return mapping[sensor]

        if name in mapping:
            return mapping[name]

        return sensor or name

    # ======================================================
    # READ TEMPERATURE
    # ======================================================

    @staticmethod
    def _read_temperature(
        path: Path,
    ) -> float | None:
        """
        Odczytuje temperaturę z pliku hwmon.
        """

        try:

            raw = float(
                path.read_text().strip()
            )

            return raw / 1000.0

        except (
            OSError,
            ValueError,
        ):

            return None

    # ======================================================
    # THERMAL ZONES
    # ======================================================

    def _collect_thermal_zones(
        self,
    ) -> list[TemperatureInfo]:
        """
        Odczytuje /sys/class/thermal.
        """

        result = []

        base = Path(
            "/sys/class/thermal"
        )

        if not base.exists():
            return result

        for zone in sorted(
            base.glob("thermal_zone*")
        ):

            temp_file = (
                zone / "temp"
            )

            temperature = (
                self._read_temperature(
                    temp_file
                )
            )

            if temperature is None:
                continue

            type_file = (
                zone / "type"
            )

            try:

                sensor_type = (
                    type_file
                    .read_text()
                    .strip()
                )

            except OSError:

                sensor_type = zone.name

            name = self._display_name(
                zone.name,
                sensor_type,
            )

            result.append(
                TemperatureInfo(
                    name=name,
                    sensor=sensor_type,
                    temperature=temperature,
                    source=str(
                        temp_file
                    ),
                )
            )

        return result

    # ======================================================
    # HWMON
    # ======================================================

    def _collect_hwmon(
        self,
    ) -> list[TemperatureInfo]:
        """
        Odczytuje temperatury z hwmon.
        """

        result = []

        base = config.HWMON_PATH

        if not base.exists():
            return result

        for hwmon in sorted(
            base.glob("hwmon*")
        ):

            name_file = (
                hwmon / "name"
            )

            try:

                hwmon_name = (
                    name_file
                    .read_text()
                    .strip()
                )

            except OSError:

                hwmon_name = hwmon.name

            for temp_file in sorted(
                hwmon.glob(
                    "temp*_input"
                )
            ):

                temperature = (
                    self._read_temperature(
                        temp_file
                    )
                )

                if temperature is None:
                    continue

                sensor_name = (
                    temp_file.name
                    .replace(
                        "_input",
                        "",
                    )
                )

                display_name = (
                    self._display_name(
                        hwmon_name,
                        sensor_name,
                    )
                )

                # Dla NVMe nazwa ma być
                # jednoznaczna.
                if hwmon_name == "nvme":

                    display_name = "NVMe"

                elif hwmon_name == "cpu_thermal":

                    display_name = "CPU"

                elif hwmon_name == "rp1_adc":

                    display_name = "RP1"

                result.append(
                    TemperatureInfo(
                        name=display_name,
                        sensor=sensor_name,
                        temperature=temperature,
                        source=str(
                            temp_file
                        ),
                    )
                )

        return result

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> TemperaturesInfo:
        """
        Pobiera komplet temperatur.
        """

        info = TemperaturesInfo()

        sensors = []

        sensors.extend(
            self._collect_thermal_zones()
        )

        sensors.extend(
            self._collect_hwmon()
        )

        # --------------------------------------------------
        # Usunięcie duplikatów.
        # --------------------------------------------------

        unique = {}

        for sensor in sensors:

            key = (
                sensor.name,
                sensor.source,
            )

            unique[key] = sensor

        info.sensors = list(
            unique.values()
        )

        # --------------------------------------------------
        # Przypisanie głównych temperatur.
        # --------------------------------------------------

        for sensor in info.sensors:

            name = sensor.name.lower()

            if name == "cpu":

                if (
                    info.cpu == 0.0
                    or sensor.temperature
                    > info.cpu
                ):
                    info.cpu = (
                        sensor.temperature
                    )

            elif name == "nvme":

                if (
                    info.nvme == 0.0
                    or sensor.temperature
                    > info.nvme
                ):
                    info.nvme = (
                        sensor.temperature
                    )

            elif name == "rp1":

                if (
                    info.rp1 == 0.0
                    or sensor.temperature
                    > info.rp1
                ):
                    info.rp1 = (
                        sensor.temperature
                    )

            elif name == "voltage":

                info.voltage = (
                    sensor.temperature
                )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================

sensor_collector = SensorCollector()