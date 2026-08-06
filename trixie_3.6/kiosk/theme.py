"""
theme.py

Warstwa prezentacji Raspberry Pi Kiosk Dashboard.

Moduł odpowiada za:

• kolory
• style Rich
• paski postępu
• formatowanie statusów
• kolorowanie temperatur
• kolorowanie użycia CPU/RAM/Dysków

Nie zawiera logiki biznesowej.
"""

from __future__ import annotations

from rich.text import Text

import config


# ==========================================================
# STYLE
# ==========================================================

HEADER_STYLE = config.COLOR_HEADER

CPU_STYLE = config.COLOR_CPU

RAM_STYLE = config.COLOR_RAM

NETWORK_STYLE = config.COLOR_NETWORK

DISK_STYLE = config.COLOR_DISK

TEMP_STYLE = config.COLOR_TEMP

SYSTEM_STYLE = config.COLOR_SYSTEM

PROXMOX_STYLE = config.COLOR_PROXMOX

PIHOLE_STYLE = config.COLOR_PIHOLE

FAN_STYLE = config.COLOR_FAN

OK_STYLE = config.COLOR_OK

WARNING_STYLE = config.COLOR_WARNING

ERROR_STYLE = config.COLOR_CRITICAL

TEXT_STYLE = config.COLOR_TEXT

DIM_STYLE = config.COLOR_DIM

BORDER_STYLE = config.COLOR_BORDER


# ==========================================================
# KOLORY PROGÓW
# ==========================================================

def usage_color(percent: float) -> str:
    """
    Zwraca kolor dla użycia CPU/RAM/Dysku.
    """

    if percent >= config.CPU_CRITICAL:
        return ERROR_STYLE

    if percent >= config.CPU_WARNING:
        return WARNING_STYLE

    return OK_STYLE


def ram_color(percent: float) -> str:

    if percent >= config.RAM_CRITICAL:
        return ERROR_STYLE

    if percent >= config.RAM_WARNING:
        return WARNING_STYLE

    return OK_STYLE


def disk_color(percent: float) -> str:

    if percent >= config.DISK_CRITICAL:
        return ERROR_STYLE

    if percent >= config.DISK_WARNING:
        return WARNING_STYLE

    return OK_STYLE


def cpu_temperature_color(temp: float) -> str:

    if temp >= config.CPU_TEMP_CRITICAL:
        return ERROR_STYLE

    if temp >= config.CPU_TEMP_WARNING:
        return WARNING_STYLE

    return OK_STYLE


def nvme_temperature_color(temp: float) -> str:

    if temp >= config.NVME_TEMP_CRITICAL:
        return ERROR_STYLE

    if temp >= config.NVME_TEMP_WARNING:
        return WARNING_STYLE

    return OK_STYLE


def rp1_temperature_color(temp: float) -> str:

    if temp >= config.RP1_TEMP_CRITICAL:
        return ERROR_STYLE

    if temp >= config.RP1_TEMP_WARNING:
        return WARNING_STYLE

    return OK_STYLE


# ==========================================================
# STATUS
# ==========================================================

def status_style(status: str) -> str:

    status = status.upper()

    if status in (
        "OK",
        "ONLINE",
        "RUNNING",
        "ACTIVE",
    ):
        return OK_STYLE

    if status in (
        "WARNING",
        "UNKNOWN",
    ):
        return WARNING_STYLE

    return ERROR_STYLE


def status_text(status: str) -> Text:

    return Text(
        status,
        style=status_style(status),
    )


# ==========================================================
# PASKI
# ==========================================================

def progress_bar(
    percent: float,
    width: int,
    color: str,
) -> str:
    """
    Buduje pasek postępu Rich.

    Przykład:

    █████████░░░░░░
    """

    percent = max(
        0,
        min(
            percent,
            100,
        ),
    )

    filled = int(
        width * percent / 100
    )

    empty = width - filled

    return (
        f"[{color}]"
        + "█" * filled
        + "[/]"
        + f"[{DIM_STYLE}]"
        + "░" * empty
        + "[/]"
    )


def cpu_bar(percent: float) -> str:

    return progress_bar(
        percent,
        config.CPU_BAR_WIDTH,
        usage_color(percent),
    )


def ram_bar(percent: float) -> str:

    return progress_bar(
        percent,
        config.RAM_BAR_WIDTH,
        ram_color(percent),
    )


def disk_bar(percent: float) -> str:

    return progress_bar(
        percent,
        config.DISK_BAR_WIDTH,
        disk_color(percent),
    )


# ==========================================================
# IKONY
# ==========================================================

def icon_cpu() -> str:
    return config.ICON_CPU


def icon_ram() -> str:
    return config.ICON_RAM


def icon_network() -> str:
    return config.ICON_NETWORK


def icon_disk() -> str:
    return config.ICON_DISK


def icon_temp() -> str:
    return config.ICON_TEMP


def icon_fan() -> str:
    return config.ICON_FAN


def icon_power() -> str:
    return config.ICON_POWER


def icon_clock() -> str:
    return config.ICON_CLOCK


def icon_pihole() -> str:
    return config.ICON_PIHOLE


def icon_proxmox() -> str:
    return config.ICON_PROXMOX


def icon_warning() -> str:
    return config.ICON_WARNING


def icon_ok() -> str:
    return config.ICON_OK


def icon_error() -> str:
    return config.ICON_ERROR


# ==========================================================
# ALERTY
# ==========================================================

def alert_style(active: bool) -> str:
    """
    Styl alarmu.
    """

    if active:
        return ERROR_STYLE

    return OK_STYLE


def alert_text(
    label: str,
    active: bool,
) -> Text:
    """
    Zwraca kolorowy napis.

    Przykład:

    CPU Temperature
    """

    return Text(
        label,
        style=alert_style(active),
    )


# ==========================================================
# PANEL
# ==========================================================

def panel_title(
    title: str,
    color: str,
) -> str:
    """
    Ujednolicone tytuły paneli.
    """

    return (
        f"[bold {color}]"
        f"{title}"
        "[/]"
    )