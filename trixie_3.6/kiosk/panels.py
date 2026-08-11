"""
panels.py

Warstwa prezentacji Raspberry Pi Kiosk Dashboard.

Ten moduł:

- otrzymuje DashboardState,
- tworzy panele Rich,
- nie wykonuje odczytów systemowych,
- nie odpytuje Proxmox,
- nie odpytuje Pi-hole,
- nie korzysta bezpośrednio z psutil.

Cała logika pobierania danych znajduje się w collectors/.
Cache danych znajduje się w services/cache.py.
"""


from __future__ import annotations

import shutil
import socket
from datetime import datetime

from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

import config

from models import (
    CPUInfo,
    DiskInfo,
    FanInfo,
    MemoryInfo,
    NetworkInfo,
    NvmeInfo,
    PiHoleInfo,
    ProxmoxContainerInfo,
    ProxmoxInfo,
    SystemInfo,
    TemperatureInfo,
    TemperaturesInfo,
)


# ==========================================================
# POMOCNICZE
# ==========================================================


def value_color(
    value: float,
    warning: float,
    critical: float,
) -> str:
    """
    Zwraca kolor zależny od wartości procentowej.
    """

    if value >= critical:
        return config.COLOR_CRITICAL

    if value >= warning:
        return config.COLOR_WARNING

    return config.COLOR_OK


def temperature_color(
    value: float,
    warning: float,
    critical: float,
) -> str:
    """
    Zwraca kolor temperatury.
    """

    if value >= critical:
        return config.COLOR_CRITICAL

    if value >= warning:
        return config.COLOR_WARNING

    return config.COLOR_OK


def fan_color(
    fan: FanInfo,
) -> str:
    """
    Zwraca kolor statusu wentylatora.
    """

    if not fan.available:
        return config.COLOR_DIM

    if fan.status == "warning":
        return config.COLOR_CRITICAL

    if fan.status == "high":
        return config.COLOR_WARNING

    if fan.status == "disabled":
        return config.COLOR_WARNING

    return config.COLOR_OK


def format_bytes(
    value: float,
) -> str:
    """
    Czytelny format rozmiaru.
    """

    if value >= 1024 ** 3:
        return f"{value / 1024 ** 3:.1f} GB"

    if value >= 1024 ** 2:
        return f"{value / 1024 ** 2:.1f} MB"

    if value >= 1024:
        return f"{value / 1024:.1f} KB"

    return f"{value:.0f} B"


def format_speed(
    value: float,
) -> str:
    """
    Czytelny format prędkości transmisji.
    """

    if value >= 1024 ** 2:
        return f"{value / 1024 ** 2:.1f} MB/s"

    if value >= 1024:
        return f"{value / 1024:.1f} KB/s"

    return f"{value:.0f} B/s"


def format_uptime(
    seconds: int,
) -> str:
    """
    Formatuje uptime.
    """

    if seconds <= 0:
        return "—"

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, _ = divmod(
        remainder,
        60,
    )

    if days:
        return (
            f"{days}d "
            f"{hours:02d}h"
        )

    if hours:
        return (
            f"{hours}h "
            f"{minutes:02d}m"
        )

    return f"{minutes}m"


def make_bar(
    value: float,
    width: int,
    color: str,
) -> str:
    """
    Tworzy prosty pasek wykorzystujący znaki terminala.
    """

    value = max(
        0.0,
        min(100.0, value),
    )

    filled = int(
        value / 100 * width
    )

    empty = width - filled

    return (
        f"[{color}]"
        + "█" * filled
        + "[/]"
        + "[dim]"
        + "░" * empty
        + "[/dim]"
    )


def panel_title(
    icon: str,
    title: str,
    color: str,
) -> str:
    """
    Wspólny format tytułów paneli.
    """

    return (
        f"[{color}]"
        f"{icon} {title}"
        f"[/]"
    )


def simple_panel(
    title: str,
    content,
    color: str,
) -> Panel:
    """
    Tworzy standardowy panel dashboardu.

    Padding jest ograniczony do minimum, aby maksymalizować
    dostępną przestrzeń roboczą terminala.
    """

    return Panel(
        content,
        title=title,
        border_style=color,
        padding=(0, 1),
        expand=True,
    )


def get_terminal_size():
    """
    Zwraca aktualny rozmiar terminala.

    Rich pracuje w kolumnach i wierszach, a nie
    w pikselach. Rozmiar jest pobierany bezpośrednio
    z terminala, na którym działa dashboard.
    """

    size = shutil.get_terminal_size(
        fallback=(
            config.DASHBOARD_MIN_WIDTH,
            config.DASHBOARD_MIN_HEIGHT,
        )
    )

    width = max(
        size.columns,
        config.DASHBOARD_MIN_WIDTH,
    )

    height = max(
        size.lines,
        config.DASHBOARD_MIN_HEIGHT,
    )

    return width, height

def get_layout_mode():
    """
    Określa sposób rozmieszczenia paneli na podstawie
    rzeczywistego rozmiaru terminala.

    Zwraca:
        "two_columns"
        "one_column"
    """

    width, height = get_terminal_size()

    if not config.DASHBOARD_RESPONSIVE:
        return "two_columns"

    if width < 120:
        return "one_column"

    if height < 32:
        return "one_column"

    return "two_columns"

# ==========================================================
# CPU
# ==========================================================


def create_cpu_panel(
    cpu: CPUInfo,
) -> Panel:
    """
    Panel CPU.

    Na małym ekranie pokazujemy każdy rdzeń,
    ale bez zbędnych kolumn.
    """

    table = Table(
        expand=True,
        box=None,
        show_header=False,
        padding=(0, 1),
    )

    table.add_column(
        "CPU",
        width=5,
        no_wrap=True,
    )

    table.add_column(
        "BAR",
        ratio=1,
        no_wrap=True,
    )

    table.add_column(
        "%",
        justify="right",
        width=5,
        no_wrap=True,
    )

    for number, usage in enumerate(
        cpu.per_core
    ):

        color = value_color(
            usage,
            config.CPU_WARNING,
            config.CPU_CRITICAL,
        )

        table.add_row(
            f"CPU{number}",
            make_bar(
                usage,
                config.CPU_BAR_WIDTH,
                color,
            ),
            (
                f"[{color}]"
                f"{usage:.0f}%"
                f"[/]"
            ),
        )

    if not cpu.per_core:

        table.add_row(
            "CPU",
            "[dim]brak danych[/]",
            "",
        )

    footer = Text()

    footer.append(
        f"AVG {cpu.usage:.1f}%  ",
        style=config.COLOR_TEXT,
    )

    if cpu.temperature > 0:

        temp_color = temperature_color(
            cpu.temperature,
            config.CPU_TEMP_WARNING,
            config.CPU_TEMP_CRITICAL,
        )

        footer.append(
            f"{cpu.temperature:.1f}°C",
            style=temp_color,
        )

    content = Group(
        table,
        footer,
    )

    return simple_panel(
        panel_title(
            config.ICON_CPU,
            "CPU",
            config.COLOR_CPU,
        ),
        content,
        config.COLOR_CPU,
    )


# ==========================================================
# RAM
# ==========================================================


def create_memory_panel(
    memory: MemoryInfo,
) -> Panel:
    """
    Panel RAM.
    """

    color = value_color(
        memory.percent,
        config.RAM_WARNING,
        config.RAM_CRITICAL,
    )

    progress = Progress(
        TextColumn(
            f"[{config.COLOR_RAM}]RAM[/]"
        ),
        BarColumn(
            bar_width=config.RAM_BAR_WIDTH,
            complete_style=color,
            finished_style=color,
        ),
        TextColumn(
            f"[{color}]"
            f"{memory.percent:.1f}%"
            f"[/]"
        ),
        expand=True,
    )

    progress.add_task(
        "RAM",
        total=100,
        completed=memory.percent,
    )

    content = Group(
        progress,
        Align.center(
            Text(
                (
                    f"{format_bytes(memory.used)}"
                    f" / "
                    f"{format_bytes(memory.total)}"
                )
            )
        ),
    )

    return simple_panel(
        panel_title(
            config.ICON_RAM,
            "RAM",
            config.COLOR_RAM,
        ),
        content,
        config.COLOR_RAM,
    )


# ==========================================================
# NETWORK
# ==========================================================


def create_network_panel(
    network: NetworkInfo,
) -> Panel:
    """
    Panel sieci.
    """

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Opis",
        ratio=1,
    )

    table.add_column(
        "Wartość",
        justify="right",
    )

    download = format_speed(
        network.download_speed
    )

    upload = format_speed(
        network.upload_speed
    )

    table.add_row(
        "[cyan]↓ DOWN[/]",
        f"[cyan]{download}[/]",
    )

    table.add_row(
        "[blue]↑ UP[/]",
        f"[blue]{upload}[/]",
    )

    if network.ip_address:

        table.add_row(
            "IP",
            network.ip_address,
        )

    if network.ping_ms > 0:

        ping_color = (
            config.COLOR_OK
            if network.ping_ms < 100
            else config.COLOR_WARNING
        )

        table.add_row(
            "PING",
            (
                f"[{ping_color}]"
                f"{network.ping_ms:.0f} ms"
                f"[/]"
            ),
        )

    internet = (
        f"[{config.COLOR_OK}]ONLINE[/]"
        if network.internet_available
        else
        f"[{config.COLOR_CRITICAL}]OFFLINE[/]"
    )

    table.add_row(
        "WAN",
        internet,
    )

    return simple_panel(
        panel_title(
            config.ICON_NETWORK,
            "SIEĆ",
            config.COLOR_NETWORK,
        ),
        table,
        config.COLOR_NETWORK,
    )


# ==========================================================
# TEMPERATURE
# ==========================================================


def create_temperature_panel(
    temperatures: TemperaturesInfo,
) -> Panel:
    """
    Panel temperatur.
    """

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Sensor",
        ratio=1,
    )

    table.add_column(
        "Temp.",
        justify="right",
        width=10,
    )

    for sensor in temperatures.sensors:

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

        color = temperature_color(
            sensor.temperature,
            warning,
            critical,
        )

        table.add_row(
            sensor.name,
            (
                f"[{color}]"
                f"{sensor.temperature:.1f} °C"
                f"[/]"
            ),
        )

    if not temperatures.sensors:

        table.add_row(
            "[dim]Brak danych[/]",
            "",
        )

    return simple_panel(
        panel_title(
            config.ICON_TEMP,
            "TEMPERATURY",
            config.COLOR_TEMP,
        ),
        table,
        config.COLOR_TEMP,
    )


# ==========================================================
# FAN
# ==========================================================


def create_fan_panel(
    fan: FanInfo,
) -> Panel:
    """
    Panel wentylatora.
    """

    if not fan.available:

        content = Align.center(
            Text(
                "WENTYLATOR NIEDOSTĘPNY",
                style=config.COLOR_DIM,
            )
        )

        return simple_panel(
            panel_title(
                config.ICON_FAN,
                "CHŁODZENIE",
                config.COLOR_FAN,
            ),
            content,
            config.COLOR_FAN,
        )

    color = fan_color(fan)

    status_names = {
        "normal": "OK",
        "high": "HIGH",
        "warning": "ALERT",
        "idle": "IDLE",
        "disabled": "OFF",
        "unknown": "?",
    }

    status = status_names.get(
        fan.status,
        fan.status.upper(),
    )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Parametr",
        ratio=1,
    )

    table.add_column(
        "Wartość",
        justify="right",
    )

    table.add_row(
        "RPM",
        (
            f"[{color}]"
            f"{fan.rpm}"
            f"[/]"
        ),
    )

    table.add_row(
        "PWM",
        f"{fan.pwm_percent:.1f}%",
    )

    table.add_row(
        "STATUS",
        (
            f"[{color}]"
            f"{status}"
            f"[/]"
        ),
    )

    return simple_panel(
        panel_title(
            config.ICON_FAN,
            "CHŁODZENIE",
            config.COLOR_FAN,
        ),
        table,
        config.COLOR_FAN,
    )


# ==========================================================
# STORAGE
# ==========================================================


def create_storage_panel(
    disks: list[DiskInfo],
) -> Panel:
    """
    Panel systemów plików.
    """

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Mount",
        ratio=1,
        no_wrap=True,
    )

    table.add_column(
        "Usage",
        justify="right",
        width=14,
        no_wrap=True,
    )

    for disk in disks:

        color = value_color(
            disk.percent,
            config.DISK_WARNING,
            config.DISK_CRITICAL,
        )

        table.add_row(
            disk.mountpoint,
            (
                f"[{color}]"
                f"{disk.percent:.0f}%"
                f"[/] "
                f"{format_bytes(disk.used)}"
                f"/"
                f"{format_bytes(disk.total)}"
            ),
        )

    if not disks:

        table.add_row(
            "[dim]Brak danych[/]",
            "",
        )

    return simple_panel(
        panel_title(
            config.ICON_DISK,
            "STORAGE",
            config.COLOR_DISK,
        ),
        table,
        config.COLOR_DISK,
    )


# ==========================================================
# NVME
# ==========================================================


def create_nvme_panel(
    nvme: NvmeInfo,
) -> Panel:
    """
    Panel NVMe.
    """

    if not nvme.available:

        content = Align.center(
            Text(
                "NVMe NIEDOSTĘPNE",
                style=config.COLOR_DIM,
            )
        )

        return simple_panel(
            "NVMe",
            content,
            config.COLOR_SYSTEM,
        )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Parametr",
        ratio=1,
    )

    table.add_column(
        "Wartość",
        justify="right",
    )

    if nvme.model:

        table.add_row(
            "MODEL",
            nvme.model,
        )

    if nvme.temperature > 0:

        color = temperature_color(
            nvme.temperature,
            config.NVME_TEMP_WARNING,
            config.NVME_TEMP_CRITICAL,
        )

        table.add_row(
            "TEMP",
            (
                f"[{color}]"
                f"{nvme.temperature:.1f} °C"
                f"[/]"
            ),
        )

    if nvme.percent_used > 0:

        color = value_color(
            nvme.percent_used,
            config.DISK_WARNING,
            config.DISK_CRITICAL,
        )

        table.add_row(
            "LIFE",
            (
                f"[{color}]"
                f"{nvme.percent_used:.0f}%"
                f"[/]"
            ),
        )

    return simple_panel(
        "NVMe",
        table,
        config.COLOR_SYSTEM,
    )


# ==========================================================
# PI-HOLE
# ==========================================================


def create_pihole_panel(
    pihole: PiHoleInfo,
) -> Panel:
    """
    Panel Pi-hole.
    """

    if not pihole.available:

        content = Align.center(
            Text(
                "PI-HOLE OFFLINE",
                style=config.COLOR_CRITICAL,
            )
        )

        return simple_panel(
            panel_title(
                config.ICON_PIHOLE,
                "PI-HOLE",
                config.COLOR_PIHOLE,
            ),
            content,
            config.COLOR_PIHOLE,
        )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Parametr",
        ratio=1,
    )

    table.add_column(
        "Wartość",
        justify="right",
    )

    dns_color = (
        config.COLOR_OK
        if pihole.dns_status.lower()
        in {
            "enabled",
            "active",
            "running",
            "ok",
        }
        else config.COLOR_WARNING
    )

    table.add_row(
        "DNS",
        (
            f"[{dns_color}]"
            f"{pihole.dns_status}"
            f"[/]"
        ),
    )

    table.add_row(
        "QUERY",
        f"{pihole.queries_total:,}",
    )

    table.add_row(
        "BLOCK",
        (
            f"{pihole.blocked_percentage:.1f}%"
        ),
    )

    table.add_row(
        "DOMAINS",
        f"{pihole.domains:,}",
    )

    table.add_row(
        "CLIENTS",
        f"{pihole.clients:,}",
    )

    return simple_panel(
        panel_title(
            config.ICON_PIHOLE,
            "PI-HOLE",
            config.COLOR_PIHOLE,
        ),
        table,
        config.COLOR_PIHOLE,
    )


# ==========================================================
# PROXMOX
# ==========================================================


def create_proxmox_panel(
    proxmox: ProxmoxInfo,
) -> Panel:
    """
    Panel Proxmox VE.
    """

    if not proxmox.available:

        content = Align.center(
            Text(
                "PROXMOX OFFLINE",
                style=config.COLOR_CRITICAL,
            )
        )

        return simple_panel(
            panel_title(
                config.ICON_PROXMOX,
                "PROXMOX",
                config.COLOR_PROXMOX,
            ),
            content,
            config.COLOR_PROXMOX,
        )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Element",
        ratio=1,
    )

    table.add_column(
        "Status",
        justify="right",
    )

    status_color = (
        config.COLOR_OK
        if proxmox.status == "running"
        else config.COLOR_WARNING
    )

    table.add_row(
        "NODE",
        (
            f"[{status_color}]"
            f"{proxmox.node}"
            f"[/]"
        ),
    )

    if proxmox.version:

        table.add_row(
            "VERSION",
            proxmox.version,
        )

    if proxmox.pihole is not None:

        pihole = proxmox.pihole

        container_color = (
            config.COLOR_OK
            if pihole.status == "running"
            else config.COLOR_CRITICAL
        )

        table.add_row(
            f"CT {pihole.vmid}",
            (
                f"[{container_color}]"
                f"{pihole.status}"
                f"[/]"
            ),
        )

    return simple_panel(
        panel_title(
            config.ICON_PROXMOX,
            "PROXMOX",
            config.COLOR_PROXMOX,
        ),
        table,
        config.COLOR_PROXMOX,
    )


# ==========================================================
# SYSTEM
# ==========================================================


def create_system_panel(
    system: SystemInfo,
) -> Panel:
    """
    Panel informacji o systemie.
    """

    hostname = (
        system.hostname
        or socket.gethostname()
    )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        "Parametr",
        ratio=1,
    )

    table.add_column(
        "Wartość",
        justify="right",
    )

    table.add_row(
        "HOST",
        hostname,
    )

    if system.architecture:

        table.add_row(
            "ARCH",
            system.architecture,
        )

    if system.uptime:

        table.add_row(
            "UPTIME",
            format_uptime(
                system.uptime
            ),
        )

    return simple_panel(
        panel_title(
            config.ICON_POWER,
            "SYSTEM",
            config.COLOR_SYSTEM,
        ),
        table,
        config.COLOR_SYSTEM,
    )


# ==========================================================
# HEADER
# ==========================================================


def create_header(
    state,
) -> Panel:
    """
    Nagłówek dashboardu.
    """

    now = datetime.now()

    title = Text(
        config.HEADER_TITLE,
        style=config.COLOR_HEADER,
        justify="center",
    )

    subtitle = Text(
        (
            f"{now.strftime(config.TIME_FORMAT)}"
            f"  •  "
            f"{state.system.hostname or 'Raspberry Pi'}"
        ),
        style="bold white",
        justify="center",
    )

    content = Group(
        title,
        subtitle,
    )

    return Panel(
        Align.center(content),
        border_style=config.COLOR_BORDER,
        padding=(0, 1),
    )


# ==========================================================
# FOOTER
# ==========================================================


def create_footer(
    state,
) -> Panel:
    """
    Stopka dashboardu.
    """

    errors = state.error_count

    if errors:

        status = Text(
            (
                f"{config.ICON_WARNING} "
                f"{errors} błędów"
            ),
            style=config.COLOR_WARNING,
        )

    else:

        status = Text(
            (
                f"{config.ICON_OK} "
                f"System OK"
            ),
            style=config.COLOR_OK,
        )

    left = Text(
        config.FOOTER_TEXT,
        style=config.COLOR_DIM,
    )

    table = Table(
        expand=True,
        box=None,
        show_header=False,
    )

    table.add_column(
        ratio=1,
    )

    table.add_column(
        justify="right",
    )

    table.add_row(
        left,
        status,
    )

    return Panel(
        table,
        border_style=config.COLOR_BORDER,
        padding=(0, 1),
    )


# ==========================================================
# GŁÓWNY LAYOUT
# ==========================================================

def create_dashboard_layout(
    state,
) -> Layout:
    """
    Tworzy kompletny layout dashboardu.

    Layout jest responsywny względem rzeczywistego
    rozmiaru terminala.

    Przy odpowiedniej szerokości używane są dwie kolumny.
    Przy małej szerokości przechodzimy do jednej kolumny.

    Program nie zakłada konkretnej rozdzielczości HDMI.
    """

    width, height = get_terminal_size()
    layout_mode = get_layout_mode()

    layout = Layout()

    # ======================================================
    # GŁÓWNY PODZIAŁ
    # ======================================================

    header_height = 4
    footer_height = 3

    body_height = max(
        1,
        height
        - header_height
        - footer_height,
    )

    layout.split_column(
        Layout(
            name="header",
            size=header_height,
        ),
        Layout(
            name="body",
            size=body_height,
        ),
        Layout(
            name="footer",
            size=footer_height,
        ),
    )

    # ======================================================
    # BODY
    # ======================================================

    if layout_mode == "two_columns":

        layout["body"].split_row(
            Layout(
                name="left",
                ratio=1,
            ),
            Layout(
                name="right",
                ratio=1,
            ),
        )

        # ==================================================
        # LEWA KOLUMNA
        # ==================================================

        layout["left"].split_column(
            Layout(
                name="cpu",
                ratio=2,
            ),
            Layout(
                name="network",
                ratio=1,
            ),
            Layout(
                name="storage",
                ratio=1,
            ),
        )

        # ==================================================
        # PRAWA KOLUMNA
        # ==================================================

        layout["right"].split_column(
            Layout(
                name="memory",
                ratio=1,
            ),
            Layout(
                name="temperature",
                ratio=1,
            ),
            Layout(
                name="cooling",
                ratio=1,
            ),
            Layout(
                name="services",
                ratio=1,
            ),
        )

    else:

        # ==================================================
        # TRYB JEDNEJ KOLUMNY
        # ==================================================

        layout["body"].split_column(
            Layout(
                name="cpu",
                ratio=2,
            ),
            Layout(
                name="network",
                ratio=1,
            ),
            Layout(
                name="storage",
                ratio=1,
            ),
            Layout(
                name="memory",
                ratio=1,
            ),
            Layout(
                name="temperature",
                ratio=1,
            ),
            Layout(
                name="cooling",
                ratio=1,
            ),
            Layout(
                name="services",
                ratio=1,
            ),
        )

    # ======================================================
    # HEADER
    # ======================================================

    layout["header"].update(
        create_header(state)
    )

    # ======================================================
    # CPU
    # ======================================================

    layout["cpu"].update(
        create_cpu_panel(
            state.cpu
        )
    )

    # ======================================================
    # NETWORK
    # ======================================================

    if config.SHOW_NETWORK_PANEL:

        layout["network"].update(
            create_network_panel(
                state.network
            )
        )

    else:

        layout["network"].update(
            Text("")
        )

    # ======================================================
    # STORAGE
    # ======================================================

    if config.SHOW_STORAGE_PANEL:

        layout["storage"].update(
            create_storage_panel(
                state.disks
            )
        )

    else:

        layout["storage"].update(
            Text("")
        )

    # ======================================================
    # RAM
    # ======================================================

    layout["memory"].update(
        create_memory_panel(
            state.memory
        )
    )

    # ======================================================
    # TEMPERATURE
    # ======================================================

    layout["temperature"].update(
        create_temperature_panel(
            state.temperatures
        )
    )

    # ======================================================
    # COOLING
    # ======================================================

    if config.SHOW_COOLING_PANEL:

        layout["cooling"].update(
            create_fan_panel(
                state.fan
            )
        )

    else:

        layout["cooling"].update(
            Text("")
        )

    # ======================================================
    # SERVICES
    # ======================================================

    services = []

    if config.SHOW_PIHOLE_PANEL:

        services.append(
            create_pihole_panel(
                state.pihole
            )
        )

    if config.SHOW_PROXMOX_PANEL:

        services.append(
            create_proxmox_panel(
                state.proxmox
            )
        )

    if services:

        layout["services"].update(
            Group(*services)
        )

    else:

        layout["services"].update(
            Text("")
        )

    # ======================================================
    # FOOTER
    # ======================================================

    layout["footer"].update(
        create_footer(state)
    )

    return layout