"""
models.py

Modele danych Raspberry Pi Kiosk Dashboard.

Moduł zawiera wyłącznie struktury danych.

Nie wykonuje:
    - odczytów systemowych,
    - komunikacji z Proxmox,
    - komunikacji z Pi-hole,
    - formatowania Rich.

Architektura:

    collectors/
        ↓
    models.py
        ↓
    services/
        ↓
    panels.py
        ↓
    dashboard.py
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ==========================================================
# CPU
# ==========================================================

@dataclass
class CPUInfo:
    """
    Informacje o procesorze.
    """

    usage: float = 0.0

    per_core: list[float] = field(
        default_factory=list
    )

    frequency_current: float = 0.0

    frequency_min: float = 0.0

    frequency_max: float = 0.0

    temperature: float = 0.0

    load_1m: float = 0.0

    load_5m: float = 0.0

    load_15m: float = 0.0

    core_count: int = 0

    physical_cores: int = 0

    architecture: str = ""

    processor_name: str = ""

    governor: str = ""

    context_switches: int = 0

    interrupts: int = 0

    soft_interrupts: int = 0

    syscalls: int = 0

    user_time: float = 0.0

    system_time: float = 0.0

    idle_time: float = 0.0


# ==========================================================
# RAM
# ==========================================================

@dataclass
class MemoryInfo:
    """
    Informacje o pamięci RAM.
    """

    total: int = 0

    used: int = 0

    available: int = 0

    free: int = 0

    percent: float = 0.0

    cached: int = 0

    buffers: int = 0

    swap_total: int = 0

    swap_used: int = 0

    swap_free: int = 0

    swap_percent: float = 0.0


# ==========================================================
# SWAP
# ==========================================================

@dataclass
class SwapInfo:
    """
    Informacje o pamięci SWAP.
    """

    total: int = 0

    used: int = 0

    free: int = 0

    percent: float = 0.0


# ==========================================================
# TEMPERATURE
# ==========================================================

@dataclass
class TemperatureInfo:
    """
    Pojedynczy odczyt temperatury.
    """

    name: str = ""

    sensor: str = ""

    temperature: float = 0.0

    source: str = ""


@dataclass
class TemperaturesInfo:
    """
    Zbiorczy stan czujników temperatury.
    """

    sensors: list[TemperatureInfo] = field(
        default_factory=list
    )

    cpu: float = 0.0

    nvme: float = 0.0

    rp1: float = 0.0

    voltage: float = 0.0


# ==========================================================
# NETWORK
# ==========================================================

@dataclass
class NetworkInfo:
    """
    Informacje o sieci.
    """

    interface: str = ""

    ip_address: str = ""

    gateway: str = ""

    dns_server: str = ""

    download_speed: float = 0.0

    upload_speed: float = 0.0

    total_download: int = 0

    total_upload: int = 0

    link_speed: int = 0

    is_up: bool = False

    ping_ms: float = 0.0

    internet_available: bool = False


# ==========================================================
# STORAGE
# ==========================================================

@dataclass
class DiskInfo:
    """
    Informacje o pojedynczym systemie plików.
    """

    mountpoint: str = ""

    device: str = ""

    filesystem: str = ""

    total: int = 0

    used: int = 0

    free: int = 0

    percent: float = 0.0

    read_speed: float = 0.0

    write_speed: float = 0.0


# ==========================================================
# NVME
# ==========================================================

@dataclass
class NvmeInfo:
    """
    Informacje o urządzeniu NVMe.
    """

    available: bool = False

    device: str = ""

    model: str = ""

    serial: str = ""

    firmware: str = ""

    temperature: float = 0.0

    percent_used: float = 0.0

    lifetime: float = 0.0

    power_on_hours: int = 0

    power_cycles: int = 0

    unsafe_shutdowns: int = 0

    media_errors: int = 0

    data_read: int = 0

    data_written: int = 0


# ==========================================================
# FAN / COOLING
# ==========================================================

@dataclass
class FanInfo:
    """
    Informacje o wentylatorze PWM.

    Przykładowy sprzęt wykryty na Raspberry Pi:

        hwmon3
        ├── name: pwmfan
        ├── fan1_input: 2948
        ├── pwm1: 75
        └── pwm1_enable: 1
    """

    available: bool = False

    device: str = ""

    hwmon_path: str = ""

    rpm: int = 0

    pwm: int = 0

    pwm_percent: float = 0.0

    pwm_enabled: int = -1

    status: str = "unknown"


# ==========================================================
# PROXMOX CONTAINER
# ==========================================================

@dataclass
class ProxmoxContainerInfo:
    """
    Informacje o pojedynczym kontenerze LXC.
    """

    vmid: int = 0

    name: str = ""

    status: str = "unknown"

    cpu: float = 0.0

    memory: int = 0

    max_memory: int = 0

    swap: int = 0

    max_swap: int = 0

    disk: int = 0

    max_disk: int = 0

    uptime: int = 0

    network_in: int = 0

    network_out: int = 0


# ==========================================================
# PROXMOX
# ==========================================================

@dataclass
class ProxmoxInfo:
    """
    Informacje o lokalnym hoście Proxmox VE.
    """

    available: bool = False

    status: str = "unknown"

    node: str = ""

    version: str = ""

    node_cpu: float = 0.0

    node_memory: int = 0

    node_max_memory: int = 0

    node_swap: int = 0

    node_max_swap: int = 0

    node_uptime: int = 0

    containers: list[
        ProxmoxContainerInfo
    ] = field(
        default_factory=list
    )

    pihole: ProxmoxContainerInfo | None = None


# ==========================================================
# PI-HOLE
# ==========================================================

@dataclass
class PiHoleInfo:
    """
    Informacje o usłudze Pi-hole.
    """

    available: bool = False

    status: str = "unknown"

    api_version: str = "unknown"

    dns_status: str = "unknown"

    response_time: float = 0.0

    queries_total: int = 0

    queries_blocked: int = 0

    blocked_percentage: float = 0.0

    domains: int = 0

    clients: int = 0

    queries_per_second: float = 0.0


# ==========================================================
# SYSTEM
# ==========================================================

@dataclass
class SystemInfo:
    """
    Informacje ogólne o systemie.
    """

    hostname: str = ""

    kernel: str = ""

    operating_system: str = ""

    architecture: str = ""

    uptime: int = 0

    boot_time: float = 0.0

    process_count: int = 0

    load_1m: float = 0.0

    load_5m: float = 0.0

    load_15m: float = 0.0


# ==========================================================
# DASHBOARD STATE
# ==========================================================

@dataclass
class DashboardState:
    """
    Kompletny stan dashboardu.

    Jest to główny obiekt przekazywany pomiędzy
    warstwą zbierającą dane a warstwą prezentacji.

    Panele nie wykonują bezpośrednich odczytów
    systemowych.
    """

    cpu: CPUInfo = field(
        default_factory=CPUInfo
    )

    memory: MemoryInfo = field(
        default_factory=MemoryInfo
    )

    temperatures: TemperaturesInfo = field(
        default_factory=TemperaturesInfo
    )

    network: NetworkInfo = field(
        default_factory=NetworkInfo
    )

    disks: list[DiskInfo] = field(
        default_factory=list
    )

    nvme: NvmeInfo = field(
        default_factory=NvmeInfo
    )

    fan: FanInfo = field(
        default_factory=FanInfo
    )

    system: SystemInfo = field(
        default_factory=SystemInfo
    )

    proxmox: ProxmoxInfo = field(
        default_factory=ProxmoxInfo
    )

    pihole: PiHoleInfo = field(
        default_factory=PiHoleInfo
    )

    # ------------------------------------------------------
    # Czas ostatniej aktualizacji poszczególnych źródeł.
    # ------------------------------------------------------

    cpu_updated: float = 0.0

    memory_updated: float = 0.0

    temperature_updated: float = 0.0

    network_updated: float = 0.0

    storage_updated: float = 0.0

    nvme_updated: float = 0.0

    fan_updated: float = 0.0

    system_updated: float = 0.0

    proxmox_updated: float = 0.0

    pihole_updated: float = 0.0

    # ------------------------------------------------------
    # Globalny czas aktualizacji.
    # ------------------------------------------------------

    last_update: float = 0.0

    # ------------------------------------------------------
    # Stan aplikacji.
    # ------------------------------------------------------

    running: bool = True

    error_count: int = 0

    last_error: str = ""