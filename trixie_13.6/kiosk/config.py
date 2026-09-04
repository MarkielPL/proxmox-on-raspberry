"""
Konfiguracja Raspberry Pi Kiosk Dashboard.

W tym pliku znajdują się wszystkie ustawienia,
które użytkownik może zmieniać bez ingerencji
w pozostały kod programu.
"""

from pathlib import Path


# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "Raspberry Pi Kiosk"
APP_VERSION = "2.2"
AUTHOR = "tom marki + ChatGPT"


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "dashboard.log"

ASSETS_DIR = PROJECT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR = ASSETS_DIR / "icons"


# ==========================================================
# FONTS / ASSETS
# ==========================================================

DASHBOARD_FONT = (
    FONTS_DIR
    / "JetBrainsMonoNLNerdFontMono-LightItalic.ttf"
)

SYMBOLS_FONT = (
    FONTS_DIR
    / "SymbolsNerdFont-Regular.ttf"
)


# ==========================================================
# PROXMOX
# ==========================================================

PROXMOX_NODE = None
# None = automatycznie pobierz hostname


# ==========================================================
# PI-HOLE
# ==========================================================

PIHOLE_CTID = 100

PIHOLE_HOST = "127.0.0.1"
PIHOLE_PORT = 80
PIHOLE_API_TOKEN = ""
PIHOLE_TIMEOUT = 2.0


# ==========================================================
# UI REFRESH
# ==========================================================

# Częstotliwość odświeżania interfejsu.
#
# WAŻNE:
# UI_REFRESH NIE określa częstotliwości collectorów.
#
# Przykład:
#
# UI_REFRESH = 0.5
# CPU_INTERVAL = 1
# PIHOLE_INTERVAL = 10
#
# oznacza:
#
# UI odświeża się co 0.5 s
# CPU pobierane jest co 1 s
# Pi-hole pobierany jest co 10 s

UI_REFRESH = 0.5

# Kompatybilność z dotychczasowym dashboard.py.
#
# Dopóki Rich pozostaje aktywny, dashboard.py może
# korzystać z tej wartości.
LIVE_REFRESH = UI_REFRESH


# ==========================================================
# COLLECTOR INTERVALS
# ==========================================================

# CPU
CPU_INTERVAL = 1.0

# Network
NETWORK_INTERVAL = 1.0

# RAM / SWAP
RAM_INTERVAL = 2.0

# System information
SYSTEM_INTERVAL = 5.0

# Temperatures
TEMPERATURE_INTERVAL = 5.0

# Disk usage
DISK_INTERVAL = 60.0

# Proxmox
PROXMOX_INTERVAL = 5.0

# Pi-hole
PIHOLE_INTERVAL = 10.0

# NVMe
NVME_INTERVAL = 5.0

# Fan
FAN_INTERVAL = 2.0


# ==========================================================
# CPU THRESHOLDS
# ==========================================================

CPU_WARNING = 60
CPU_CRITICAL = 85


# ==========================================================
# RAM THRESHOLDS
# ==========================================================

RAM_WARNING = 70
RAM_CRITICAL = 90


# ==========================================================
# TEMPERATURE THRESHOLDS
# ==========================================================

CPU_TEMP_WARNING = 65
CPU_TEMP_CRITICAL = 80

NVME_TEMP_WARNING = 55
NVME_TEMP_CRITICAL = 70

RP1_TEMP_WARNING = 60
RP1_TEMP_CRITICAL = 80


# ==========================================================
# DISK THRESHOLDS
# ==========================================================

DISK_WARNING = 75
DISK_CRITICAL = 90


# ==========================================================
# FAN
# ==========================================================

FAN_MIN_RPM = 500
FAN_WARNING_RPM = 1500

PWM_MAX = 255

FAN_HWMON_NAME = "pwmfan"
FAN_INPUT_NAME = "fan1_input"
FAN_PWM_NAME = "pwm1"
FAN_PWM_ENABLE_NAME = "pwm1_enable"


# ==========================================================
# UI BAR WIDTHS
# ==========================================================

CPU_BAR_WIDTH = 20
RAM_BAR_WIDTH = 30
DISK_BAR_WIDTH = 25
FAN_BAR_WIDTH = 20


# ==========================================================
# COLORS
# ==========================================================

COLOR_HEADER = "bold white on dark_blue"

COLOR_CPU = "cyan"
COLOR_RAM = "magenta"
COLOR_NETWORK = "blue"
COLOR_DISK = "green"
COLOR_TEMP = "yellow"
COLOR_SYSTEM = "bright_cyan"
COLOR_PROXMOX = "bright_magenta"
COLOR_PIHOLE = "bright_green"
COLOR_FAN = "bright_blue"

COLOR_OK = "green"
COLOR_WARNING = "yellow"
COLOR_CRITICAL = "bold red"

COLOR_TEXT = "white"
COLOR_DIM = "grey62"
COLOR_BORDER = "grey50"


# ==========================================================
# ICONS
# ==========================================================

ICON_CPU = "🖥"
ICON_RAM = "🧠"
ICON_NETWORK = "🌐"
ICON_DISK = "💾"
ICON_TEMP = "🌡"
ICON_FAN = "🌀"
ICON_POWER = "⚡"
ICON_CLOCK = "🕒"
ICON_PIHOLE = "🛡"
ICON_PROXMOX = "📦"
ICON_WARNING = "⚠"
ICON_OK = "✔"
ICON_ERROR = "✖"


# ==========================================================
# SYSTEM PATHS
# ==========================================================

CPU_TEMP_PATH = Path(
    "/sys/class/thermal/thermal_zone0/temp"
)

HWMON_PATH = Path(
    "/sys/class/hwmon"
)


# ==========================================================
# FILESYSTEMS
# ==========================================================

IGNORED_FILESYSTEMS = {
    "tmpfs",
    "devtmpfs",
    "proc",
    "sysfs",
    "cgroup",
    "cgroup2",
    "overlay",
    "squashfs",
    "tracefs",
    "debugfs",
    "devpts",
    "mqueue",
    "securityfs",
}


# ==========================================================
# TEMPERATURE SENSOR NAMES
# ==========================================================

TEMPERATURE_NAMES = {
    "cpu_thermal": "CPU",
    "thermal_zone0": "CPU",
    "nvme": "NVMe",
    "Composite": "NVMe",
    "Sensor 1": "NVMe",
    "rp1_adc": "RP1",
    "rpi_volt": "Voltage",
    "pwmfan": "Fan",
}


# ==========================================================
# ALERTS / LOGGING
# ==========================================================

ENABLE_SOUND_ALERT = False
ENABLE_POPUP_ALERT = True
ENABLE_LOGGING = True


# ==========================================================
# PANEL VISIBILITY
# ==========================================================

SHOW_PIHOLE_PANEL = True
SHOW_NETWORK_PANEL = True
SHOW_STORAGE_PANEL = True
SHOW_SYSTEM_PANEL = True
SHOW_COOLING_PANEL = True
SHOW_PROXMOX_PANEL = True

SHOW_BOOT_PARTITION = True
SHOW_TMPFS = False


# ==========================================================
# NETWORK TESTS
# ==========================================================

PING_TARGET = "1.1.1.1"
DNS_TEST_HOST = "google.com"


# ==========================================================
# DATE / TIME
# ==========================================================

TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==========================================================
# UI TEXT
# ==========================================================

HEADER_TITLE = (
    "Raspberry Pi 5 • Debian Trixie • Proxmox VE 9"
)

FOOTER_TEXT = "Kiosk Dashboard"