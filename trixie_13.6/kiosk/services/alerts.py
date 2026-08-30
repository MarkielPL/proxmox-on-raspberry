"""
System ostrzeżeń Raspberry Pi Kiosk Dashboard.

Moduł analizuje DashboardState i tworzy listę aktywnych
ostrzeżeń.

Nie renderuje UI.
Nie wyświetla komunikatów.
Nie steruje sprzętem.
"""

from __future__ import annotations

from dataclasses import dataclass

import config

from models import DashboardState


# ==========================================================
# MODEL ALERTU
# ==========================================================


@dataclass
class Alert:
    """
    Pojedyncze ostrzeżenie.
    """

    source: str

    message: str

    severity: str

    value: float | None = None


# ==========================================================
# ALERT MANAGER
# ==========================================================


class AlertManager:
    """
    Analizuje stan dashboardu pod kątem alarmów.
    """

    def __init__(self) -> None:

        self.alerts: list[Alert] = []

    # ======================================================
    # CPU
    # ======================================================

    def _check_cpu(
        self,
        state: DashboardState,
    ) -> None:

        cpu = state.cpu.usage

        if cpu >= config.CPU_CRITICAL:

            self.alerts.append(
                Alert(
                    source="CPU",
                    message=(
                        f"CPU usage "
                        f"{cpu:.1f}%"
                    ),
                    severity="critical",
                    value=cpu,
                )
            )

        elif cpu >= config.CPU_WARNING:

            self.alerts.append(
                Alert(
                    source="CPU",
                    message=(
                        f"CPU usage "
                        f"{cpu:.1f}%"
                    ),
                    severity="warning",
                    value=cpu,
                )
            )

    # ======================================================
    # RAM
    # ======================================================

    def _check_memory(
        self,
        state: DashboardState,
    ) -> None:

        ram = state.memory.percent

        if ram >= config.RAM_CRITICAL:

            self.alerts.append(
                Alert(
                    source="RAM",
                    message=(
                        f"RAM usage "
                        f"{ram:.1f}%"
                    ),
                    severity="critical",
                    value=ram,
                )
            )

        elif ram >= config.RAM_WARNING:

            self.alerts.append(
                Alert(
                    source="RAM",
                    message=(
                        f"RAM usage "
                        f"{ram:.1f}%"
                    ),
                    severity="warning",
                    value=ram,
                )
            )

    # ======================================================
    # TEMPERATURY
    # ======================================================

    def _check_temperatures(
        self,
        state: DashboardState,
    ) -> None:

        for sensor in (
            state.temperatures.sensors
        ):

            warning = (
                config.CPU_TEMP_WARNING
            )

            critical = (
                config.CPU_TEMP_CRITICAL
            )

            if sensor.name == "NVMe":

                warning = (
                    config.NVME_TEMP_WARNING
                )

                critical = (
                    config.NVME_TEMP_CRITICAL
                )

            elif sensor.name == "RP1":

                warning = (
                    config.RP1_TEMP_WARNING
                )

                critical = (
                    config.RP1_TEMP_CRITICAL
                )

            temperature = (
                sensor.temperature
            )

            if temperature >= critical:

                self.alerts.append(
                    Alert(
                        source=sensor.name,
                        message=(
                            f"{sensor.name} "
                            f"{temperature:.1f} °C"
                        ),
                        severity="critical",
                        value=temperature,
                    )
                )

            elif temperature >= warning:

                self.alerts.append(
                    Alert(
                        source=sensor.name,
                        message=(
                            f"{sensor.name} "
                            f"{temperature:.1f} °C"
                        ),
                        severity="warning",
                        value=temperature,
                    )
                )

    # ======================================================
    # DYSKI
    # ======================================================

    def _check_disks(
        self,
        state: DashboardState,
    ) -> None:

        for disk in state.disks:

            if (
                disk.percent
                >= config.DISK_CRITICAL
            ):

                self.alerts.append(
                    Alert(
                        source="DISK",
                        message=(
                            f"{disk.mountpoint} "
                            f"{disk.percent:.1f}%"
                        ),
                        severity="critical",
                        value=disk.percent,
                    )
                )

            elif (
                disk.percent
                >= config.DISK_WARNING
            ):

                self.alerts.append(
                    Alert(
                        source="DISK",
                        message=(
                            f"{disk.mountpoint} "
                            f"{disk.percent:.1f}%"
                        ),
                        severity="warning",
                        value=disk.percent,
                    )
                )

    # ======================================================
    # FAN
    # ======================================================

    def _check_fan(
        self,
        state: DashboardState,
    ) -> None:

        fan = state.fan

        if not fan.available:
            return

        if fan.status == "warning":

            self.alerts.append(
                Alert(
                    source="FAN",
                    message=(
                        "PWM active but "
                        "fan is not rotating"
                    ),
                    severity="critical",
                    value=fan.rpm,
                )
            )

        elif (
            fan.rpm < config.FAN_MIN_RPM
            and fan.pwm > 0
        ):

            self.alerts.append(
                Alert(
                    source="FAN",
                    message=(
                        f"Low RPM: "
                        f"{fan.rpm}"
                    ),
                    severity="warning",
                    value=fan.rpm,
                )
            )

    # ======================================================
    # PROXMOX
    # ======================================================

    def _check_proxmox(
        self,
        state: DashboardState,
    ) -> None:

        proxmox = state.proxmox

        if not proxmox.available:

            self.alerts.append(
                Alert(
                    source="PROXMOX",
                    message="Proxmox unavailable",
                    severity="critical",
                )
            )

            return

        if proxmox.pihole is not None:

            if (
                proxmox.pihole.status
                != "running"
            ):

                self.alerts.append(
                    Alert(
                        source="PIHOLE",
                        message=(
                            f"CT "
                            f"{proxmox.pihole.vmid} "
                            f"is not running"
                        ),
                        severity="critical",
                    )
                )

    # ======================================================
    # PI-HOLE
    # ======================================================

    def _check_pihole(
        self,
        state: DashboardState,
    ) -> None:

        pihole = state.pihole

        if not pihole.available:

            self.alerts.append(
                Alert(
                    source="PIHOLE",
                    message="Pi-hole unavailable",
                    severity="warning",
                )
            )

            return

        if pihole.dns_status.lower() not in {
            "enabled",
            "active",
            "running",
            "ok",
        }:

            self.alerts.append(
                Alert(
                    source="PIHOLE",
                    message=(
                        f"DNS status: "
                        f"{pihole.dns_status}"
                    ),
                    severity="warning",
                )
            )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def check(
        self,
        state: DashboardState,
    ) -> list[Alert]:
        """
        Wykonuje kompletną analizę stanu.
        """

        self.alerts = []

        self._check_cpu(state)

        self._check_memory(state)

        self._check_temperatures(state)

        self._check_disks(state)

        self._check_fan(state)

        self._check_proxmox(state)

        self._check_pihole(state)

        return list(
            self.alerts
        )

    # ======================================================
    # STATUS
    # ======================================================

    def has_critical(
        self,
    ) -> bool:

        return any(
            alert.severity == "critical"
            for alert in self.alerts
        )

    def has_warning(
        self,
    ) -> bool:

        return any(
            alert.severity == "warning"
            for alert in self.alerts
        )

    def is_ok(
        self,
    ) -> bool:

        return not self.alerts


# ==========================================================
# GLOBALNA INSTANCJA
# ==========================================================


alert_manager = AlertManager()