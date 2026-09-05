"""
Monitoring temperatur Raspberry Pi.

Źródła:

    /sys/class/thermal
    /sys/class/hwmon
    psutil.sensors_temperatures()

Priorytet źródeł:

    1. /sys/class/thermal
    2. /sys/class/hwmon
    3. psutil jako fallback

Obsługiwane między innymi:

    cpu_thermal
    nvme
    rp1_adc
    rpi_volt
    pwmfan
"""


from __future__ import annotations

from pathlib import Path

import psutil

import config

from models import (
    TemperatureInfo,
    TemperaturesInfo,
)


class SensorCollector:
    """
    Kolektor temperatur i czujników sprzętowych.
    """

    THERMAL_PATH = Path(
        "/sys/class/thermal"
    )

    HWMON_PATH = Path(
        "/sys/class/hwmon"
    )

    # ======================================================
    # READ TEMPERATURE
    # ======================================================

    @staticmethod
    def _read_temperature(
        path: Path,
    ) -> float | None:
        """
        Czyta temperaturę w milistopniach C.
        """

        try:

            raw = float(
                path.read_text(
                    encoding="utf-8"
                ).strip()
            )

            return raw / 1000.0

        except (
            OSError,
            ValueError,
        ):

            return None

    # ======================================================
    # NAME
    # ======================================================

    @staticmethod
    def _map_name(
        name: str,
    ) -> str:
        """
        Zamienia techniczną nazwę czujnika
        na nazwę przyjazną dla dashboardu.
        """

        return config.TEMPERATURE_NAMES.get(
            name,
            name,
        )

    # ======================================================
    # THERMAL ZONES
    # ======================================================

    def _collect_thermal_zones(
        self,
    ) -> list[TemperatureInfo]:
        """
        Odczytuje /sys/class/thermal/thermal_zone*.
        """

        result: list[TemperatureInfo] = []

        if not self.THERMAL_PATH.exists():
            return result

        for zone in sorted(
            self.THERMAL_PATH.glob(
                "thermal_zone*"
            )
        ):

            temperature = (
                self._read_temperature(
                    zone / "temp"
                )
            )

            if temperature is None:
                continue

            zone_name = zone.name

            type_path = zone / "type"

            try:

                sensor_type = (
                    type_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )

            except OSError:

                sensor_type = zone_name

            name = self._map_name(
                sensor_type
            )

            result.append(
                TemperatureInfo(
                    name=name,
                    sensor=sensor_type,
                    temperature=temperature,
                    source=zone_name,
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
        Odczytuje czujniki temperatury z hwmon.
        """

        result: list[TemperatureInfo] = []

        if not self.HWMON_PATH.exists():
            return result

        for hwmon in sorted(
            self.HWMON_PATH.glob(
                "hwmon*"
            )
        ):

            name_path = hwmon / "name"

            try:

                sensor_name = (
                    name_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )

            except OSError:

                sensor_name = hwmon.name

            mapped_name = self._map_name(
                sensor_name
            )

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

                result.append(
                    TemperatureInfo(
                        name=mapped_name,
                        sensor=temp_file.stem,
                        temperature=temperature,
                        source=sensor_name,
                    )
                )

        return result

    # ======================================================
    # PSUTIL
    # ======================================================

    @staticmethod
    def _collect_psutil() -> list[TemperatureInfo]:
        """
        Odczytuje temperatury dostępne przez psutil.

        psutil jest traktowane jako fallback.
        """

        result: list[TemperatureInfo] = []

        try:

            sensor_data = (
                psutil.sensors_temperatures(
                    fahrenheit=False
                )
            )

        except (
            AttributeError,
            OSError,
        ):

            return result

        for group, sensors in sensor_data.items():

            for sensor in sensors:

                temperature = sensor.current

                if temperature is None:
                    continue

                label = (
                    sensor.label
                    or group
                )

                result.append(
                    TemperatureInfo(
                        name=config.TEMPERATURE_NAMES.get(
                            label,
                            label,
                        ),
                        sensor=label,
                        temperature=float(
                            temperature
                        ),
                        source=group,
                    )
                )

        return result

    # ======================================================
    # DEDUPLICATION
    # ======================================================

    @staticmethod
    def _deduplicate(
        sensors: list[TemperatureInfo],
    ) -> list[TemperatureInfo]:
        """
        Usuwa duplikaty sensorów.

        Priorytet:

        - pierwszy sensor zachowuje miejsce,
        - identyczna nazwa prezentacyjna nie jest
          dodawana ponownie.

        Dzięki temu np. CPU wykryte przez:

            thermal_zone
            hwmon
            psutil

        nie pojawi się trzy razy.
        """

        result: list[TemperatureInfo] = []

        seen_names: set[str] = set()

        for item in sensors:

            name = item.name.strip()

            if not name:
                continue

            key = name.lower()

            if key in seen_names:
                continue

            seen_names.add(key)
            result.append(item)

        return result

    # ======================================================
    # COLLECT
    # ======================================================

    def collect(self) -> TemperaturesInfo:
        """
        Pobiera kompletny stan temperatur.

        Preferowane są bezpośrednie źródła sysfs.

        psutil jest używane tylko jako fallback,
        jeżeli sysfs nie dostarczył żadnych danych.
        """

        info = TemperaturesInfo()

        sensors: list[TemperatureInfo] = []

        # --------------------------------------------------
        # 1. THERMAL ZONES
        # --------------------------------------------------

        thermal_sensors = (
            self._collect_thermal_zones()
        )

        sensors.extend(
            thermal_sensors
        )

        # --------------------------------------------------
        # 2. HWMON
        # --------------------------------------------------

        hwmon_sensors = (
            self._collect_hwmon()
        )

        sensors.extend(
            hwmon_sensors
        )

        # --------------------------------------------------
        # 3. PSUTIL FALLBACK
        # --------------------------------------------------

        # Jeżeli sysfs nie dostarczył żadnych danych,
        # dopiero wtedy korzystamy z psutil.

        if not sensors:

            sensors.extend(
                self._collect_psutil()
            )

        # --------------------------------------------------
        # DEDUPLIKACJA
        # --------------------------------------------------

        unique = self._deduplicate(
            sensors
        )

        info.sensors = unique

        # --------------------------------------------------
        # KATEGORIE GŁÓWNE
        # --------------------------------------------------

        for sensor in unique:

            name = sensor.name.strip().lower()

            if name == "cpu":

                if info.cpu == 0.0:

                    info.cpu = (
                        sensor.temperature
                    )

            elif name == "nvme":

                if info.nvme == 0.0:

                    info.nvme = (
                        sensor.temperature
                    )

            elif name == "rp1":

                if info.rp1 == 0.0:

                    info.rp1 = (
                        sensor.temperature
                    )

            elif name == "voltage":

                # Voltage nie powinien być
                # temperaturą, ale pozostawiamy
                # zgodność z konfiguracją.

                info.voltage = (
                    sensor.temperature
                )

        return info


sensor_collector = SensorCollector()