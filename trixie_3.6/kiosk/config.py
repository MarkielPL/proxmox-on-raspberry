"""
Konfiguracja Raspberry Pi Kiosk Dashboard.

W tym pliku znajdują się wszystkie ustawienia,
które użytkownik może zmieniać bez ingerencji
w pozostały kod programu.
"""

from pathlib import Path


# ==========================================================
# INFORMACJE O APLIKACJI
# ==========================================================

APP_NAME = "Raspberry Pi Kiosk"

APP_VERSION = "2.2"

AUTHOR = "tom marki + ChatGPT"


# ==========================================================
# ŚCIEŻKI
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

LOG_DIR = PROJECT_DIR / "logs"

LOG_FILE = LOG_DIR / "dashboard.log"

# ==========================================================
# ASSETS
# ==========================================================

ASSETS_DIR = PROJECT_DIR / "assets"

FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR = ASSETS_DIR / "icons"

DASHBOARD_FONT = (
    FONTS_DIR
    / "JetBrainsMonoNerdFontMono-Regular.ttf"
)

SYMBOLS_FONT = (
    FONTS_DIR
    / "SymbolsNerdFont-Regular.ttf"
)

# ==========================================================
# PROXMOX
# ==========================================================

PROXMOX_NODE = None

# None = automatycznie pobierz hostname.

PIHOLE_CTID = 100

# ID kontenera LXC z Pi-hole.


# ==========================================================
# PI-HOLE
# ==========================================================

PIHOLE_HOST = "127.0.0.1"

# Adres IP Pi-hole.
#
# UWAGA:
# Jeżeli Pi-hole działa w CT100 i ma własny adres IP,
# tutaj należy wpisać adres IP tego kontenera.
#
# Przykład:
#
# PIHOLE_HOST = "192.168.1.10"


PIHOLE_PORT = 80

# Port HTTP API Pi-hole.


PIHOLE_API_TOKEN = ""

# Token API Pi-hole.
#
# Dla konfiguracji bez uwierzytelniania pozostaw:
#
# ""


PIHOLE_TIMEOUT = 2.0

# Maksymalny czas oczekiwania na odpowiedź API.


# ==========================================================
# ODŚWIEŻANIE
# ==========================================================

LIVE_REFRESH = 2

CPU_INTERVAL = 1

NETWORK_INTERVAL = 1

RAM_INTERVAL = 2

SYSTEM_INTERVAL = 5

TEMPERATURE_INTERVAL = 5

DISK_INTERVAL = 60

PROXMOX_INTERVAL = 5

PIHOLE_INTERVAL = 10

NVME_INTERVAL = 5

FAN_INTERVAL = 2

# ==========================================================
# ROZMIAR I DOPASOWANIE DASHBOARDU
# ==========================================================

# Minimalna szerokość terminala, dla której dashboard
# jest projektowany.
DASHBOARD_MIN_WIDTH = 120

# Minimalna wysokość terminala.
DASHBOARD_MIN_HEIGHT = 32

# Margines bezpieczeństwa od krawędzi terminala.
DASHBOARD_MARGIN = 0

# Czy dashboard ma automatycznie dopasowywać layout
# do aktualnego rozmiaru terminala.
DASHBOARD_AUTO_RESIZE = True

# Maksymalna liczba kolumn głównego layoutu.
DASHBOARD_COLUMNS = 2

# Czy układ ma przełączać się na jedną kolumnę,
# gdy terminal jest zbyt wąski.
DASHBOARD_RESPONSIVE = True

# ==========================================================
# PROGI CPU
# ==========================================================

CPU_WARNING = 60

CPU_CRITICAL = 85


# ==========================================================
# RAM
# ==========================================================

RAM_WARNING = 70

RAM_CRITICAL = 90


# ==========================================================
# TEMPERATURY
# ==========================================================

CPU_TEMP_WARNING = 65

CPU_TEMP_CRITICAL = 80

NVME_TEMP_WARNING = 55

NVME_TEMP_CRITICAL = 70

RP1_TEMP_WARNING = 60

RP1_TEMP_CRITICAL = 80


# ==========================================================
# DYSKI
# ==========================================================

DISK_WARNING = 75

DISK_CRITICAL = 90


# ==========================================================
# WENTYLATOR
# ==========================================================

FAN_MIN_RPM = 500

FAN_WARNING_RPM = 1500

PWM_MAX = 255

# Ścieżka hwmon wentylatora.
#
# Na Twoim RPi5 wcześniej wykryliśmy:
#
# /sys/class/hwmon/hwmon3
#     name = pwmfan
#     fan1_input = 2948
#     pwm1 = 75
#     pwm1_enable = 1
#
# Dlatego NIE wpisujemy tutaj hwmon3 na sztywno.
# Kolektor będzie wyszukiwał urządzenie po nazwie "pwmfan".

FAN_HWMON_NAME = "pwmfan"

FAN_INPUT_NAME = "fan1_input"

FAN_PWM_NAME = "pwm1"

FAN_PWM_ENABLE_NAME = "pwm1_enable"


# ==========================================================
# PASKI
# ==========================================================

CPU_BAR_WIDTH = 16

RAM_BAR_WIDTH = 20

DISK_BAR_WIDTH = 18

FAN_BAR_WIDTH = 16


# ==========================================================
# KOLORY
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
# IKONY
# ==========================================================

# ICON_CPU = "🖥"

# ICON_RAM = "🧠"

# ICON_NETWORK = "🌐"

# ICON_DISK = "💾"

# ICON_TEMP = "🌡"

# ICON_FAN = "🌀"

# ICON_POWER = "⚡"

# ICON_CLOCK = "🕒"

# ICON_PIHOLE = "🛡"

# ICON_PROXMOX = "📦"

# ICON_WARNING = "⚠"

# ICON_OK = "✔"

# ICON_ERROR = "✖"

ICON_CPU = "CPU"
ICON_RAM = "RAM"
ICON_NETWORK = "NET"
ICON_DISK = "DISK"
ICON_TEMP = "TEMP"
ICON_FAN = "FAN"
ICON_POWER = "SYS"
ICON_CLOCK = "TIME"
ICON_PIHOLE = "DNS"
ICON_PROXMOX = "PVE"

ICON_WARNING = "!"
ICON_OK = "+"
ICON_ERROR = "X"


# ==========================================================
# PLIKI SYSTEMOWE
# ==========================================================

CPU_TEMP_PATH = Path(
    "/sys/class/thermal/thermal_zone0/temp"
)

HWMON_PATH = Path(
    "/sys/class/hwmon"
)


# ==========================================================
# IGNOROWANE SYSTEMY PLIKÓW
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
# MAPOWANIE CZUJNIKÓW
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
# ALERTY
# ==========================================================

ENABLE_SOUND_ALERT = False

ENABLE_POPUP_ALERT = True

ENABLE_LOGGING = True


# ==========================================================
# PANEL PI-HOLE
# ==========================================================

SHOW_PIHOLE_PANEL = True

SHOW_NETWORK_PANEL = True

SHOW_STORAGE_PANEL = True

SHOW_SYSTEM_PANEL = True

SHOW_COOLING_PANEL = True

SHOW_PROXMOX_PANEL = True


# ==========================================================
# PANEL DYSKÓW
# ==========================================================

SHOW_BOOT_PARTITION = True

SHOW_TMPFS = False


# ==========================================================
# SIEĆ
# ==========================================================

PING_TARGET = "1.1.1.1"

DNS_TEST_HOST = "google.com"


# ==========================================================
# FORMATY
# ==========================================================

TIME_FORMAT = "%H:%M:%S"

DATE_FORMAT = "%Y-%m-%d"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==========================================================
# NAGŁÓWEK
# ==========================================================

HEADER_TITLE = (
    "Raspberry Pi 5 | Debian Trixie | Proxmox VE 9"
)

FOOTER_TEXT = "Kiosk Dashboard"