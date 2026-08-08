"""
collectors/sensors.py

Odczyt temperatur z:

/sys/class/thermal
/sys/class/hwmon

Obsługiwane są m.in.:

- CPU
- NVMe
- RP1
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
    """Collector temperatur."""

    def _read_temperature(
        self,
        path: Path,
    ) -> float | None:

        try:

            value = float(
                path.read_text().strip()
            )

        except (
            OSError,
            ValueError,
        ):

            return None

        # Linux thermal zones zwykle
        # zwracają temperaturę w milikelwinach.
        if value > 1000:
            value /= 1000

        return value

    # ======================================================
    # THERMAL
    # ======================================================

    def _collect_thermal_zones(
        self,
    ) -> list[TemperatureInfo]:

        result = []

        thermal_path = Path(
            "/sys/class/thermal"
        )

        if not thermal_path.exists():
            return result

        for zone in sorted(
            thermal_path.glob(
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

            zone_type = ""

            try:

                zone_type = (
                    zone / "type"
                ).read_text().strip()

            except OSError:

                pass

            name = (
                config.TEMPERATURE_NAMES.get(
                    zone_type,
                    config.TEMPERATURE_NAMES.get(
                        zone.name,
                        zone_type
                        or zone.name,
                    ),
                )
            )

            result.append(
                TemperatureInfo(
                    name=name,
                    temperature=temperature,
                    source=str(zone),
                )
            )

        return result

    # ======================================================
    # HWMON
    # ======================================================

    def _collect_hwmon(
        self,
    ) -> list[TemperatureInfo]:

        result = []

        hwmon_path = config.HWMON_PATH

        if not hwmon_path.exists():
            return result

        for hwmon in sorted(
            hwmon_path.glob("hwmon*")
        ):

            name_file = hwmon / "name"

            try:

                group = (
                    name_file
                    .read_text()
                    .strip()
                )

            except OSError:

                continue

            if group == "pwmfan":
                continue

            for temp_file in sorted(
                hwmon.glob("temp*_input")
            ):

                temperature = (
                    self._read_temperature(
                        temp_file
                    )
                )

                if temperature is None:
                    continue

                label_file = (
                    temp_file.parent
                    / (
                        temp_file.name
                        .replace(
                            "_input",
                            "_label",
                        )
                    )
                )

                label = ""

                try:

                    label = (
                        label_file
                        .read_text()
                        .strip()
                    )

                except OSError:

                    pass

                sensor_name = (
                    label
                    or config.TEMPERATURE_NAMES.get(
                        group,
                        group,
                    )
                )

                result.append(
                    TemperatureInfo(
                        name=sensor_name,
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

    def collect(
        self,
    ) -> TemperaturesInfo:

        sensors = []

        sensors.extend(
            self._collect_thermal_zones()
        )

        sensors.extend(
            self._collect_hwmon()
        )

        # Usuwamy duplikaty po nazwie,
        # pozostawiając ostatni odczyt.
        unique = {}

        for sensor in sensors:

            unique[sensor.name] = sensor

        return TemperaturesInfo(
            sensors=list(
                unique.values()
            )
        )


sensor_collector = SensorCollector()