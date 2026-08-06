"""
Modele danych używane przez Raspberry Pi Kiosk Dashboard.

Wszystkie moduły projektu korzystają z poniższych struktur
zamiast zwracać słowniki.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ==========================================================
# CPU
# ==========================================================

@dataclass(slots=True)
class CpuInfo:
    """Informacje o procesorze."""

    usage_total: float = 0.0

    usage_per_core: list[float] = field(default_factory=list)

    frequency: float = 0.0

    load1: float = 0.0

    load5: float = 0.0

    load15: float = 0.0


# ==========================================================
# RAM
# ==========================================================

@dataclass(slots=True)
class MemoryInfo:
    """Informacje o pamięci RAM."""

    total: int = 0

    available: int = 0

    used: int = 0

    free: int = 0

    cached: int = 0

    buffers: int = 0

    percent: float = 0.0


# ==========================================================
# SWAP
# ==========================================================

@dataclass(slots=True)
class SwapInfo:
    """Informacje o pamięci SWAP."""

    total: int = 0

    used: int = 0

    free: int = 0

    percent: float = 0.0


# ==========================================================
# NETWORK
# ==========================================================

@dataclass(slots=True)
class NetworkInfo:
    """Statystyki sieci."""

    download_speed: float = 0.0

    upload_speed: float = 0.0

    total_download: int = 0

    total_upload: int = 0

    ip_address: str = ""

    gateway: str = ""

    dns_server: str = ""

    interface: str = ""


# ==========================================================
# STORAGE
# ==========================================================

@dataclass(slots=True)
class DiskInfo:
    """Informacje o jednym systemie plików."""

    mountpoint: str = ""

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

@dataclass(slots=True)
class NvmeInfo:
    """Informacje o dysku NVMe."""

    model: str = ""

    serial: str = ""

    temperature: float = 0.0

    percent_used: float = 0.0

    lifetime: float = 0.0


# ==========================================================
# TEMPERATURY
# ==========================================================

@dataclass(slots=True)
class TemperatureInfo:
    """Temperatury systemowe."""

    cpu: float = 0.0

    nvme: float = 0.0

    rp1: float = 0.0

    voltage: float = 0.0


# ==========================================================
# WENTYLATOR
# ==========================================================

@dataclass(slots=True)
class FanInfo:
    """Stan wentylatora."""

    available: bool = False

    rpm: int = 0

    pwm: int = 0

    pwm_percent: float = 0.0

    pwm_mode: int = 0

    device: str = ""


# ==========================================================
# ZASILANIE
# ==========================================================

@dataclass(slots=True)
class PowerInfo:
    """Status zasilania Raspberry Pi."""

    status: str = "UNKNOWN"

    throttled: bool = False

    undervoltage: bool = False

    frequency_capped: bool = False

    temperature_limit: bool = False

    message: str = ""


# ==========================================================
# SYSTEM
# ==========================================================

@dataclass(slots=True)
class SystemInfo:
    """Informacje o systemie."""

    hostname: str = ""

    kernel: str = ""

    distribution: str = ""

    architecture: str = ""

    uptime: str = ""

    boot_time: float = 0.0

    current_time: str = ""

    current_date: str = ""


# ==========================================================
# PROXMOX
# ==========================================================

@dataclass(slots=True)
class ProxmoxInfo:
    """Stan hosta Proxmox."""

    node: str = ""

    version: str = ""

    running_vms: int = 0

    running_lxc: int = 0

    cpu: float = 0.0

    memory: float = 0.0

    storage: float = 0.0

    healthy: bool = True


# ==========================================================
# PI-HOLE
# ==========================================================

@dataclass(slots=True)
class PiHoleInfo:
    """Stan kontenera Pi-hole."""

    available: bool = False

    vmid: int = 0

    hostname: str = ""

    status: str = "UNKNOWN"

    uptime: str = ""

    cpu: float = 0.0

    memory: int = 0

    memory_percent: float = 0.0

    disk_percent: float = 0.0

    ip: str = ""

    dns_online: bool = False

    ping: float = 0.0

    api_online: bool = False

    queries: int = 0

    blocked: int = 0

    clients: int = 0


# ==========================================================
# ALERTY
# ==========================================================

@dataclass(slots=True)
class AlertInfo:
    """Stan wszystkich alarmów."""

    cpu_temperature: bool = False

    nvme_temperature: bool = False

    disk_full: bool = False

    ram_full: bool = False

    undervoltage: bool = False

    throttled: bool = False

    fan_failure: bool = False

    pihole_offline: bool = False

    dns_failure: bool = False

    internet_failure: bool = False


# ==========================================================
# DASHBOARD
# ==========================================================

@dataclass(slots=True)
class DashboardState:
    """
    Główny stan aplikacji.

    Jest jedynym obiektem przekazywanym pomiędzy modułami.
    """

    cpu: CpuInfo = field(default_factory=CpuInfo)

    memory: MemoryInfo = field(default_factory=MemoryInfo)

    swap: SwapInfo = field(default_factory=SwapInfo)

    network: NetworkInfo = field(default_factory=NetworkInfo)

    disks: list[DiskInfo] = field(default_factory=list)

    nvme: NvmeInfo = field(default_factory=NvmeInfo)

    temperatures: TemperatureInfo = field(default_factory=TemperatureInfo)

    fan: FanInfo = field(default_factory=FanInfo)

    power: PowerInfo = field(default_factory=PowerInfo)

    system: SystemInfo = field(default_factory=SystemInfo)

    proxmox: ProxmoxInfo = field(default_factory=ProxmoxInfo)

    pihole: PiHoleInfo = field(default_factory=PiHoleInfo)

    alerts: AlertInfo = field(default_factory=AlertInfo)

    last_update: datetime = field(default_factory=datetime.now)