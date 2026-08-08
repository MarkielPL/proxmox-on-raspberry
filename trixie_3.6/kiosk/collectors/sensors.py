"""
Odczyt temperatur i czujników sprzętowych Raspberry Pi.

Moduł odpowiada wyłącznie za odczyt danych z:

    /sys/class/thermal
    /sys/class/hwmon

Nie tworzy paneli Rich.
Nie wykonuje formatowania tekstu.

Obsługiwane źródła:

    cpu_thermal
    nvme
    rp1_adc
    rpi_volt
    inne czujniki udostępnione przez hwmon
"""

from __future__ import annotations

from pathlib import Path

from models import TemperatureInfo
from models import TemperaturesInfo

import config


class SensorCollector:
    """
    Kolektor temperatur i czujników sprzętowych.
    """

    def __init__(self) -> None:
        self.hwmon_path = Path(
            config.HWMON_PATH
        )

        self.thermal_path = Path(
            "/sys/class/thermal"
        )

    # ======================================================
    # PLIK SENSOR
    # ======================================================

    @staticmethod
    def read_sensor_value(
        path: Path,
    ) -> float | None:
        """
        Odczytuje wartość czujnika.

        Obsługiwane są typowe wartości hwmon
        zapisane w:

            millidegree Celsius

        czyli np.:

            45000 → 45.0 °C
        """

        try:

            value = float(
                path.read_text(
                    encoding="utf-8"
                ).strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return None

        # hwmon temperaturę podaje zwykle
        # w tysięcznych częściach stopnia.
        if abs(value) > 1000:
            value /= 1000.0

        return value

    # ======================================================
    # HWMON NAME
    # ======================================================

    @staticmethod
    def read_hwmon_name(
        path: Path,
    ) -> str:
        """
        Odczytuje nazwę urządzenia hwmon.
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
    # TEMPERATURE NAME
    # ======================================================

    @staticmethod
    def map_temperature_name(
        hwmon_name: str,
        sensor_label: str,
        fallback: str,
    ) -> str:
        """
        Zamienia techniczną nazwę czujnika
        na nazwę prezentowaną w dashboardzie.

        Najpierw sprawdzamy etykietę czujnika,
        następnie nazwę urządzenia hwmon.
        """

        if sensor_label:

            mapped = (
                config.TEMPERATURE_NAMES.get(
                    sensor_label
                )
            )

            if mapped:
                return mapped

        if hwmon_name:

            mapped = (
                config.TEMPERATURE_NAMES.get(
                    hwmon_name
                )
            )

            if mapped:
                return mapped

        return fallback

    # ======================================================
    # THERMAL ZONES
    # ======================================================

    def collect_thermal_zones(
        self,
    ) -> list[TemperatureInfo]:
        """
        Odczytuje temperatury z:

            /sys/class/thermal/thermal_zone*

        """

        sensors: list[
            TemperatureInfo
        ] = []

        if not self.thermal_path.exists():
            return sensors

        for zone in sorted(
            self.thermal_path.glob(
                "thermal_zone*"
            )
        ):

            temperature_file = (
                zone / "temp"
            )

            if not temperature_file.is_file():
                continue

            temperature = (
                self.read_sensor_value(
                    temperature_file
                )
            )

            if temperature is None:
                continue

            try:

                zone_type = (
                    zone / "type"
                ).read_text(
                    encoding="utf-8"
                ).strip()

            except OSError:

                zone_type = ""

            name = (
                config.TEMPERATURE_NAMES.get(
                    zone_type
                )
                or config.TEMPERATURE_NAMES.get(
                    zone.name
                )
                or zone_type
                or zone.name
            )

            sensors.append(
                TemperatureInfo(
                    name=name,
                    sensor=zone.name,
                    temperature=temperature,
                    source="thermal",
                )
            )

        return sensors

    # ======================================================
    # HWMON
    # ======================================================

    def collect_hwmon(
        self,
    ) -> list[TemperatureInfo]:
        """
        Odczytuje temperatury z urządzeń hwmon.

        Szukane są pliki:

            temp*_input

        """

        sensors: list[
            TemperatureInfo
        ] = []

        if not self.hwmon_path.exists():
            return sensors

        for hwmon in sorted(
            self.hwmon_path.glob(
                "hwmon*"
            )
        ):

            if not hwmon.is_dir():
                continue

            hwmon_name = (
                self.read_hwmon_name(
                    hwmon / "name"
                )
            )

            for temp_file in sorted(
                hwmon.glob(
                    "temp*_input"
                )
            ):

                temperature = (
                    self.read_sensor_value(
                        temp_file
                    )
                )

                if temperature is None:
                    continue

                sensor_number = (
                    temp_file.name
                    .replace(
                        "_input",
                        "",
                    )
                )

                label_file = (
                    hwmon
                    / f"{sensor_number}_label"
                )

                try:

                    sensor_label = (
                        label_file.read_text(
                            encoding="utf-8"
                        ).strip()
                    )

                except OSError:

                    sensor_label = ""

                fallback = (
                    sensor_label
                    or hwmon_name
                    or sensor_number
                )

                name = (
                    self.map_temperature_name(
                        hwmon_name,
                        sensor_label,
                        fallback,
                    )
                )

                sensors.append(
                    TemperatureInfo(
                        name=name,
                        sensor=(
                            f"{hwmon_name}:"
                            f"{sensor_number}"
                        ),
                        temperature=temperature,
                        source="hwmon",
                    )
                )

        return sensors

    # ======================================================
    # DUPLIKATY
    # ======================================================

    @staticmethod
    def remove_duplicates(
        sensors: list[TemperatureInfo],
    ) -> list[TemperatureInfo]:
        """
        Usuwa duplikaty temperatur.

        Raspberry Pi może udostępniać tę samą
        temperaturę zarówno przez thermal_zone,
        jak i hwmon.

        Preferujemy pierwszy znaleziony odczyt.
        """

        result: list[
            TemperatureInfo
        ] = []

        seen: set[
            tuple[str, str]
        ] = set()

        for sensor in sensors:

            key = (
                sensor.name,
                sensor.sensor,
            )

            if key in seen:
                continue

            seen.add(key)

            result.append(sensor)

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

        # Najpierw thermal zones.
        sensors.extend(
            self.collect_thermal_zones()
        )

        # Następnie hwmon.
        sensors.extend(
            self.collect_hwmon()
        )

        info.sensors = (
            self.remove_duplicates(
                sensors
            )
        )

        # --------------------------------------------------
        # Przypisanie najważniejszych temperatur
        # do pól szybkiego dostępu.
        # --------------------------------------------------

        for sensor in info.sensors:

            name = sensor.name.lower()

            if (
                name == "cpu"
                or "cpu" in name
            ):

                if info.cpu == 0.0:
                    info.cpu = (
                        sensor.temperature
                    )

            elif "nvme" in name:

                if info.nvme == 0.0:
                    info.nvme = (
                        sensor.temperature
                    )

            elif "rp1" in name:

                if info.rp1 == 0.0:
                    info.rp1 = (
                        sensor.temperature
                    )

            elif (
                "volt" in name
                or "voltage" in name
            ):

                if info.voltage == 0.0:
                    info.voltage = (
                        sensor.temperature
                    )

        return info


# ==========================================================
# GLOBALNY COLLECTOR
# ==========================================================


sensor_collector = SensorCollector()