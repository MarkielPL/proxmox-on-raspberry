#!/usr/bin/env python3

"""
Główny program Raspberry Pi Kiosk Dashboard.

Odpowiada wyłącznie za:

- uruchomienie aplikacji,
- cykl odświeżania,
- pobieranie danych z CollectorManager,
- renderowanie interfejsu,
- bezpieczne zakończenie programu.

Logika zbierania danych znajduje się w:

    collectors/

Zarządzanie danymi:

    services/collector_manager.py

Buforowanie i kontrola interwałów:

    services/cache.py

Modele danych:

    models.py

Interfejs:

    panels.py
"""

from __future__ import annotations

import sys
import time

from rich.console import Console
from rich.live import Live

import config

from services.collector_manager import collector_manager


# ==========================================================
# KONSOLE
# ==========================================================

console = Console()


# ==========================================================
# INFORMACJA STARTOWA
# ==========================================================

def print_startup() -> None:
    """
    Wyświetla krótką informację podczas uruchamiania.
    """

    console.print()

    console.print(
        f"[bold cyan]"
        f"{config.APP_NAME}"
        f"[/]"
    )

    console.print(
        f"[dim]"
        f"Version {config.APP_VERSION}"
        f"[/]"
    )

    console.print(
        f"[dim]"
        f"Starting dashboard..."
        f"[/]"
    )

    console.print()


# ==========================================================
# PANEL GŁÓWNY
# ==========================================================

def create_dashboard(state):
    """
    Tworzy kompletny interfejs dashboardu.

    Cała logika layoutu znajduje się
    w panels.py.

    dashboard.py nie zna szczegółów
    poszczególnych paneli.
    """

    from panels import create_dashboard_layout

    return create_dashboard_layout(
        state
    )


# ==========================================================
# GŁÓWNA PĘTLA
# ==========================================================

def run() -> None:
    """
    Uruchamia główną pętlę dashboardu.
    """

    print_startup()

    # ------------------------------------------------------
    # Pierwsze pobranie danych
    # ------------------------------------------------------

    state = collector_manager.force_update()

    # ------------------------------------------------------
    # Live
    # ------------------------------------------------------

    with Live(
        create_dashboard(state),
        console=console,
        screen=True,
        refresh_per_second=4,
        transient=False,
    ) as live:

        try:

            while True:

                cycle_started = time.monotonic()

                # ------------------------------------------
                # Aktualizacja danych
                # ------------------------------------------

                state = collector_manager.update()

                # ------------------------------------------
                # Renderowanie
                # ------------------------------------------

                live.update(
                    create_dashboard(
                        state
                    ),
                    refresh=True,
                )

                # ------------------------------------------
                # Stabilny interwał
                # ------------------------------------------

                elapsed = (
                    time.monotonic()
                    - cycle_started
                )

                sleep_time = max(
                    0.05,
                    config.LIVE_REFRESH
                    - elapsed,
                )

                time.sleep(
                    sleep_time
                )

        except KeyboardInterrupt:

            pass


# ==========================================================
# MAIN
# ==========================================================

def main() -> int:
    """
    Punkt wejścia programu.
    """

    try:

        run()

    except KeyboardInterrupt:

        return 0

    except Exception as error:

        console.print(
            "\n"
            "[bold red]"
            "Dashboard error:"
            "[/] "
            f"{error}"
        )

        return 1

    return 0


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )