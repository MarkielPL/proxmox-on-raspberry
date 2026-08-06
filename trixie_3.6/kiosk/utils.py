"""
Funkcje pomocnicze używane przez cały projekt.

Moduł nie zawiera żadnej logiki biznesowej.
Służy wyłącznie do:

- formatowania danych,
- odczytu plików,
- uruchamiania poleceń,
- konwersji jednostek.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


# ==========================================================
# ODCZYT PLIKÓW
# ==========================================================

def read_text(path: str | Path, default: str = "") -> str:
    """
    Odczytuje zawartość pliku tekstowego.

    Zwraca wartość domyślną w przypadku błędu.
    """

    try:
        return Path(path).read_text().strip()

    except (
        FileNotFoundError,
        PermissionError,
        OSError,
    ):
        return default


def read_int(path: str | Path, default: int = 0) -> int:
    """
    Odczytuje liczbę całkowitą z pliku.
    """

    try:
        return int(read_text(path))

    except ValueError:
        return default


def read_float(path: str | Path, default: float = 0.0) -> float:
    """
    Odczytuje liczbę zmiennoprzecinkową.
    """

    try:
        return float(read_text(path))

    except ValueError:
        return default


# ==========================================================
# SYSTEM
# ==========================================================

def run_command(
    command: list[str],
    timeout: float = 2.0,
) -> str:
    """
    Uruchamia polecenie systemowe.

    Nie zgłasza wyjątków.
    """

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return result.stdout.strip()

    except (
        subprocess.TimeoutExpired,
        OSError,
    ):

        return ""


# ==========================================================
# FORMATOWANIE
# ==========================================================

def format_bytes(value: float) -> str:
    """
    Zamienia bajty na czytelną postać.
    """

    units = (
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    )

    size = float(value)

    for unit in units:

        if size < 1024:

            if unit == "B":
                return f"{size:.0f} {unit}"

            return f"{size:.1f} {unit}"

        size /= 1024

    return f"{size:.1f} PB"


def format_speed(value: float) -> str:
    """
    Format transferu.
    """

    return f"{format_bytes(value)}/s"


def format_percent(value: float) -> str:
    """
    Zaokrąglenie procentów.
    """

    return f"{value:.1f}%"


def format_frequency(value: float) -> str:
    """
    MHz / GHz.
    """

    if value >= 1000:
        return f"{value/1000:.2f} GHz"

    return f"{value:.0f} MHz"


def format_temperature(value: float) -> str:
    """
    Temperatura.
    """

    return f"{value:.1f} °C"


# ==========================================================
# CZAS
# ==========================================================

def format_uptime(seconds: float) -> str:
    """
    Zamienia sekundy na:

    12d 03h
    """

    seconds = int(seconds)

    days = seconds // 86400

    hours = (seconds % 86400) // 3600

    minutes = (seconds % 3600) // 60

    if days:

        return f"{days}d {hours:02d}h"

    return f"{hours:02d}h {minutes:02d}m"


def monotonic() -> float:
    """
    Skrót do time.monotonic().
    """

    return time.monotonic()


# ==========================================================
# KONWERSJE
# ==========================================================

def pwm_to_percent(
    pwm: int,
    maximum: int = 255,
) -> float:
    """
    PWM -> %
    """

    if maximum <= 0:
        return 0.0

    return pwm / maximum * 100


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Ogranicza wartość do zadanego zakresu.
    """

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


# ==========================================================
# BOOL
# ==========================================================

def bool_to_text(value: bool) -> str:
    """
    True -> TAK

    False -> NIE
    """

    return "TAK" if value else "NIE"


def bool_to_status(value: bool) -> str:
    """
    True -> OK

    False -> ERROR
    """

    return "OK" if value else "ERROR"