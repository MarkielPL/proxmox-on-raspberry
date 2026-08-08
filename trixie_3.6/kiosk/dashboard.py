#!/usr/bin/env python3

"""
Główny program Raspberry Pi Kiosk Dashboard.

Odpowiada wyłącznie za:

- uruchomienie aplikacji,
- cykl odświeżania,
- pobieranie danych z cache,
- renderowanie interfejsu,
- bezpieczne zakończenie programu.

Logika zbierania danych znajduje się w:

    collectors/

Buforowanie:

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

from services.cache import dashboard_cache


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

    Docelowo cała logika layoutu będzie znajdowała się
    w panels.py.

    dashboard.py nie powinien znać szczegółów
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

    state = dashboard_cache.update()

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

                cycle_started = (
                    time.monotonic()
                )

                # ------------------------------------------
                # Aktualizacja cache
                # ------------------------------------------

                state = (
                    dashboard_cache.update()
                )

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
            f"\n"
            f"[bold red]"
            f"Dashboard error:"
            f"[/] "
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