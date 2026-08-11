# Raspberry Pi Kiosk Dashboard

> **Modularny dashboard systemowy dla Raspberry Pi 5**, uruchamiany w trybie kiosk na terminalu tekstowym.
>
> Projekt został zaprojektowany jako lekki, modularny i odporny na błędy interfejs monitorujący system Raspberry Pi, Proxmox VE, Pi-hole, pamięć masową, sieć oraz układ chłodzenia.
---
<img width="1182" height="638" alt="{EFF87572-FE4F-4018-88D6-FE30679045D5}" src="https://github.com/user-attachments/assets/e8829688-8bd1-4a61-838f-659f1d6a04b7" />

---

## 📌 Status projektu

**Wersja:** `2.2`  
**Platforma docelowa:** Raspberry Pi 5 8 GB  
**System:** Debian GNU/Linux 13 (Trixie)  
**Kernel:** Linux 6.18.x / aarch64  
**Virtualizacja:** Proxmox VE 9  
**Interfejs:** terminal / Rich  
**Tryb pracy:** kiosk / daemon  
**Docelowy ekran:** mały ekran dotykowy

Projekt jest rozwijany etapami. Obecna architektura stanowi bazę pod dalszą rozbudowę bez konieczności przebudowy całego programu.

---

# 1. 🎯 Cel projektu

Raspberry Pi Kiosk Dashboard ma prezentować w jednym, czytelnym interfejsie najważniejsze informacje dotyczące urządzenia.

Dashboard obecnie obsługuje m.in.:

- obciążenie CPU,
- obciążenie poszczególnych rdzeni,
- temperatury,
- pamięć RAM,
- SWAP,
- sieć,
- adres IP,
- ping i dostęp do Internetu,
- systemy plików i zajętość dysków,
- temperaturę oraz stan NVMe,
- wentylator PWM / RPM,
- Proxmox VE,
- kontener Pi-hole,
- status Pi-hole,
- uptime,
- informacje systemowe,
- obsługę błędów collectorów,
- centralny cache danych,
- niezależne interwały aktualizacji,
- logowanie błędów.

Warstwa prezentacji korzysta z biblioteki **Rich**, dzięki czemu interfejs może być renderowany bezpośrednio w terminalu.

---

# 2. 🏗️ Architektura projektu

Projekt jest podzielony na kilka odpowiedzialności:

```text
┌──────────────────────────────┐
│         SYSTEM / HW          │
│                              │
│ psutil / /proc / /sys        │
│ Proxmox API                  │
│ Pi-hole API                  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         collectors/          │
│                              │
│ CPU                          │
│ Memory                       │
│ Network                      │
│ Sensors                      │
│ Fan                          │
│ Storage                      │
│ NVMe                         │
│ System                       │
│ Proxmox                      │
│ Pi-hole                      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       services/cache.py      │
│                              │
│ centralny cache              │
│ interwały aktualizacji       │
│ ostatnie poprawne dane       │
│ błędy                        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ services/collector_manager.py│
│                              │
│ orkiestracja collectorów     │
│ obsługa błędów               │
│ aktualizacja DashboardState  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           models.py          │
│                              │
│ DashboardState               │
│ CPUInfo / MemoryInfo / ...   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           panels.py          │
│                              │
│ Rich Panels                  │
│ Tables                       │
│ Layout                       │
│ formatowanie danych          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         dashboard.py         │
│                              │
│ Live                         │
│ główna pętla                 │
│ odświeżanie UI               │
└──────────────────────────────┘
```

### Główna zasada

**Collector nie powinien wiedzieć nic o wyglądzie dashboardu.**

**Panel nie powinien wiedzieć, skąd pochodzą dane.**

**Dashboard nie powinien implementować logiki pobierania danych.**

Dzięki temu można rozwijać poszczególne elementy niezależnie.

---

# 3. 🔄 Schemat przepływu danych

```text
              SYSTEM
                 │
                 ▼
        ┌─────────────────┐
        │    Collector    │
        └────────┬────────┘
                 │
                 │ wynik
                 ▼
        ┌─────────────────┐
        │      Cache      │
        └────────┬────────┘
                 │
                 │ aktualna wartość
                 ▼
        ┌─────────────────┐
        │ CollectorManager│
        └────────┬────────┘
                 │
                 │ model danych
                 ▼
        ┌─────────────────┐
        │ DashboardState  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │     panels.py   │
        └────────┬────────┘
                 │
                 │ Rich Layout
                 ▼
        ┌─────────────────┐
        │   dashboard.py  │
        └────────┬────────┘
                 │
                 ▼
              TERMINAL
```

---

# 4. 🧠 Schemat logiki programu

Program pracuje w cyklu:

```text
START
  │
  ▼
Załaduj config.py
  │
  ▼
Utwórz CollectorManager / DashboardState
  │
  ▼
Pierwsza aktualizacja danych
  │
  ▼
Utwórz Rich Live
  │
  ▼
┌───────────────────────────────┐
│          GŁÓWNA PĘTLA         │
│                               │
│  1. Sprawdź interwały         │
│  2. Uruchom wymagane collectory│
│  3. Zapisz wyniki do cache    │
│  4. Zaktualizuj state         │
│  5. Zbuduj layout             │
│  6. Renderuj Live              │
│  7. Odczekaj do kolejnego cyklu│
│                               │
└───────────────┬───────────────┘
                │
                └──────────────► powtórz
```

Każdy collector może działać z własnym interwałem.

Przykładowo:

```text
CPU          → 1 s
Network      → 1 s
RAM          → 2 s
Fan          → 2 s
Temperature  → 5 s
NVMe         → 5 s
System       → 5 s
Proxmox      → 5 s
Pi-hole      → 10 s
Storage      → 60 s
```

Dzięki temu nie ma potrzeby wykonywania cięższych operacji przy każdym odświeżeniu interfejsu.

---

# 5. 📁 Drzewo projektu

Aktualne drzewo projektu przedstawia się następująco:

```text
kiosk/
│
├── config.py
├── dashboard.py
├── models.py
├── panels.py
│
├── collectors/
│   ├── __init__.py
│   ├── cpu.py
│   ├── fan.py
│   ├── memory.py
│   ├── network.py
│   ├── nvme.py
│   ├── pihole.py
│   ├── proxmox.py
│   ├── sensors.py
│   ├── storage.py
│   └── system.py
│
├── services/
│   ├── __init__.py
│   ├── cache.py
│   └── collector_manager.py
│
├── assets/
│   ├── fonts/
│   │   ├── JetBrainsMonoNLNerdFontMono-LightItalic.ttf
│   │   └── SymbolsNerdFont-Regular.ttf
│   │
│   ├── images/
│   │
│   └── icons/
│
└── logs/
    └── dashboard.log
```

> `logs/` oraz zawartość katalogów `assets/images/` i `assets/icons/` mogą zmieniać się w czasie działania projektu.

---

# 6. 📦 Opis głównych plików

## `config.py`

Centralna konfiguracja aplikacji.

Znajdują się tutaj m.in.:

- informacje o aplikacji,
- ścieżki projektu,
- katalog `assets/`,
- ścieżki fontów,
- konfiguracja Proxmox,
- konfiguracja Pi-hole,
- interwały aktualizacji,
- progi alarmowe,
- konfiguracja wentylatora,
- szerokości pasków,
- kolory,
- ikony,
- ścieżki systemowe,
- ignorowane systemy plików,
- konfiguracja paneli,
- formaty daty i czasu.

**Założenie:** użytkownik powinien móc zmieniać zachowanie dashboardu przede wszystkim tutaj, bez ingerencji w kod aplikacji.

---

## `models.py`

Definiuje modele danych przekazywane pomiędzy warstwami.

Przykładowe modele:

```text
DashboardState
CPUInfo
MemoryInfo
NetworkInfo
TemperatureInfo
TemperaturesInfo
FanInfo
DiskInfo
NvmeInfo
PiHoleInfo
ProxmoxInfo
ProxmoxContainerInfo
SystemInfo
```

Modele oddzielają **dane** od sposobu ich prezentacji.

---

## `collectors/`

Warstwa pobierania danych.

Każdy moduł odpowiada za określony obszar systemu.

### `cpu.py`

Pobiera informacje o CPU.

Źródła obejmują m.in.:

- `psutil`,
- `/proc/cpuinfo`,
- `/sys/devices/system/cpu/`.

Collector może dostarczać m.in.:

- całkowite użycie CPU,
- użycie poszczególnych rdzeni,
- liczbę rdzeni,
- architekturę,
- nazwę procesora,
- governor,
- częstotliwość,
- load average,
- statystyki CPU.

### `memory.py`

Pobiera:

- RAM,
- SWAP.

### `network.py`

Pobiera informacje sieciowe:

- adres IP,
- transfer,
- ping,
- dostępność Internetu.

### `sensors.py`

Odpowiada za odczyt czujników temperatury.

W konfiguracji zdefiniowane są m.in.:

```text
CPU
NVMe
RP1
Voltage
Fan
```

### `fan.py`

Obsługuje dane wentylatora:

- RPM,
- PWM,
- status.

Collector wyszukuje urządzenie `hwmon` po nazwie, zamiast zakładać stały numer `hwmonX`.

### `storage.py`

Pobiera informacje o systemach plików i zajętości przestrzeni.

### `nvme.py`

Pobiera informacje dotyczące NVMe, w tym temperaturę i stan nośnika.

### `system.py`

Pobiera informacje systemowe, np.:

- hostname,
- architekturę,
- uptime.

### `proxmox.py`

Pobiera informacje o środowisku Proxmox VE.

### `pihole.py`

Pobiera informacje z Pi-hole.

---

# 7. ⚙️ `services/`

Warstwa logiki aplikacyjnej.

## `cache.py`

Centralny mechanizm cache.

Odpowiada za:

- przechowywanie ostatnich danych,
- kontrolowanie czasu aktualizacji,
- sprawdzanie `needs_update()`,
- przechowywanie błędów,
- umożliwienie niezależnych interwałów collectorów.

Istotną zasadą jest zachowanie ostatniej poprawnej wartości w przypadku chwilowego błędu źródła.

---

## `collector_manager.py`

Centralny orkiestrator collectorów.

Odpowiada za:

1. sprawdzenie cache,
2. sprawdzenie interwału,
3. uruchomienie właściwego collectora,
4. zapis wyniku,
5. aktualizację `DashboardState`,
6. obsługę wyjątków,
7. logowanie błędów.

Nie odpowiada za:

- Rich,
- wygląd paneli,
- formatowanie,
- layout.

Schemat:

```text
collector
    │
    ▼
 cache
    │
    ▼
CollectorManager
    │
    ▼
DashboardState
```

Błąd pojedynczego collectora nie powinien zatrzymać całego dashboardu.

---

# 8. 🎨 `panels.py`

Warstwa prezentacji.

Moduł:

- otrzymuje `DashboardState`,
- tworzy komponenty Rich,
- buduje panele,
- buduje layout,
- formatuje wartości,
- dobiera kolory,
- nie wykonuje bezpośrednich odczytów systemowych.

Przykładowe panele:

```text
CPU
RAM
SIEĆ
STORAGE
TEMPERATURY
CHŁODZENIE
NVMe
PI-HOLE
PROXMOX
SYSTEM
```

Centralny layout jest również budowany tutaj.

Dzięki temu `dashboard.py` pozostaje możliwie prosty.

---

# 9. 🖥️ `dashboard.py`

Punkt wejścia aplikacji i główna pętla programu.

Odpowiada za:

- start programu,
- komunikat startowy,
- pobranie stanu,
- uruchomienie `Rich.Live`,
- cykliczne aktualizowanie danych,
- renderowanie dashboardu,
- obsługę zakończenia programu.

Schemat:

```text
dashboard.py
     │
     ├── dashboard_cache.update()
     │
     ├── create_dashboard(state)
     │
     ├── Live.update(...)
     │
     └── sleep(LIVE_REFRESH)
              │
              └──────► kolejny cykl
```

---

# 10. 🖼️ Assets

Katalog:

```text
assets/
├── fonts/
├── images/
└── icons/
```

jest przeznaczony na zasoby zewnętrzne wykorzystywane przez aplikację.

Obecnie:

```text
assets/fonts/
├── JetBrainsMonoNLNerdFontMono-LightItalic.ttf
└── SymbolsNerdFont-Regular.ttf
```

### Przeznaczenie

`JetBrainsMonoNLNerdFontMono-LightItalic.ttf`

→ główny font projektu.

`SymbolsNerdFont-Regular.ttf`

→ symbole i znaki Nerd Font.

W przyszłości `assets/` może zawierać np.:

```text
images/
    logo.png
    background.png

icons/
    cpu.svg
    network.svg
    storage.svg
```

---

# 11. 🧩 Warstwy odpowiedzialności

Projekt można traktować jako sześć logicznych warstw:

```text
┌─────────────────────────────┐
│  1. HARDWARE / SYSTEM       │
│  Linux / sysfs / proc       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  2. COLLECTORS              │
│  Pobieranie danych          │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  3. CACHE / SERVICES        │
│  Harmonogram + odporność    │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  4. MODELS / STATE          │
│  Ujednolicone dane          │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  5. PRESENTATION             │
│  Rich / panels / layout     │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  6. APPLICATION LOOP        │
│  dashboard.py / Live        │
└─────────────────────────────┘
```

---

# 12. 🛡️ Odporność na błędy

Jedną z podstawowych zasad projektu jest:

> **Awaria jednego źródła danych nie może zatrzymać całego dashboardu.**

Przykład:

```text
Pi-hole API
     │
     X  timeout
     │
     ▼
CollectorError
     │
     ▼
CollectorManager
     │
     ├── zapis błędu
     ├── zwiększenie error_count
     └── zachowanie ostatnich poprawnych danych
              │
              ▼
         Dashboard działa dalej
```

Błędy mogą być zapisywane do:

```text
logs/dashboard.log
```

---

# 13. ⏱️ System interwałów

Dashboard posiada dwa niezależne pojęcia czasu:

### Częstotliwość renderowania

Sterowana przez:

```python
LIVE_REFRESH
```

### Częstotliwość pobierania danych

Sterowana osobno dla każdego collectora:

```python
CPU_INTERVAL
NETWORK_INTERVAL
RAM_INTERVAL
TEMPERATURE_INTERVAL
DISK_INTERVAL
PROXMOX_INTERVAL
PIHOLE_INTERVAL
NVME_INTERVAL
FAN_INTERVAL
```

To rozdzielenie jest celowe.

Terminal może być odświeżany często, podczas gdy np. informacje o zajętości dysku nie muszą być pobierane równie często.

---

# 14. 🎛️ Konfiguracja UI

Wygląd dashboardu jest w dużej części kontrolowany przez `config.py`.

Przykładowo:

```python
CPU_BAR_WIDTH = 20
RAM_BAR_WIDTH = 30
DISK_BAR_WIDTH = 25
FAN_BAR_WIDTH = 20
```

oraz:

```python
COLOR_CPU
COLOR_RAM
COLOR_NETWORK
COLOR_DISK
COLOR_TEMP
COLOR_SYSTEM
COLOR_PROXMOX
COLOR_PIHOLE
COLOR_FAN
```

Widoczność paneli:

```python
SHOW_PIHOLE_PANEL = True
SHOW_NETWORK_PANEL = True
SHOW_STORAGE_PANEL = True
SHOW_SYSTEM_PANEL = True
SHOW_COOLING_PANEL = True
SHOW_PROXMOX_PANEL = True
```

Dzięki temu podstawowa konfiguracja interfejsu nie wymaga modyfikowania `panels.py`.

---

# 15. 🧱 Zasady rozwoju projektu

Przy dalszej rozbudowie należy zachować następujące reguły:

### Collector

```text
TAK:
- pobiera dane,
- zwraca model,
- obsługuje specyfikę źródła.

NIE:
- Rich,
- Panel,
- Layout,
- formatowanie UI.
```

### Cache / services

```text
TAK:
- harmonogram,
- cache,
- koordynacja,
- błędy.

NIE:
- wygląd UI.
```

### Models

```text
TAK:
- struktura danych,
- stan aplikacji.

NIE:
- pobieranie danych,
- renderowanie.
```

### Panels

```text
TAK:
- prezentacja,
- formatowanie,
- layout,
- kolory.

NIE:
- psutil,
- sysfs,
- API Proxmox,
- API Pi-hole.
```

### Dashboard

```text
TAK:
- lifecycle aplikacji,
- Live,
- główna pętla.

NIE:
- implementacja collectorów,
- logika pojedynczych paneli.
```

---

# 16. 🚀 Kierunek dalszej ewolucji

Projekt jest przygotowany do dalszej rozbudowy bez zmiany podstawowego przepływu danych:

```text
NOWE ŹRÓDŁO
    │
    ▼
NOWY COLLECTOR
    │
    ▼
MODEL DANYCH
    │
    ▼
CACHE / MANAGER
    │
    ▼
NOWY PANEL
    │
    ▼
LAYOUT
```

Możliwe przyszłe kierunki rozwoju obejmują m.in.:

- dalsze rozbudowanie panelu CPU,
- szczegółowe informacje o NVMe,
- monitoring sieci,
- dodatkowe sensory,
- historię wartości,
- wykresy,
- rozbudowane alerty,
- konfigurację layoutu,
- obsługę dodatkowych usług,
- ulepszenie obsługi fontów i assetów,
- tryby widoku,
- interakcję dotykową,
- diagnostykę systemu,
- testy automatyczne.

Istotne jest, aby nowe funkcje były dokładane do odpowiednich warstw zamiast zwiększać odpowiedzialność `dashboard.py` lub `panels.py`.

---

# 17. 🧭 Model mentalny projektu

Najprostszy sposób rozumienia aplikacji:

```text
              "SKĄD?"
                 │
                 ▼
            COLLECTORS
                 │
                 ▼
              "CO?"
                 │
                 ▼
         MODELS / STATE
                 │
                 ▼
             "KIEDY?"
                 │
                 ▼
          CACHE / MANAGER
                 │
                 ▼
             "JAK?"
                 │
                 ▼
             PANELS
                 │
                 ▼
             "GDZIE?"
                 │
                 ▼
           DASHBOARD
                 │
                 ▼
             TERMINAL
```

---

# 18. 📄 Licencja

Na obecnym etapie projekt nie deklaruje konkretnej licencji open-source.

Przed publikacją repozytorium należy dodać odpowiedni plik:

```text
LICENSE
```

zgodnie z wybraną licencją projektu.

---

# 19. 👤 Autor

**tom marki + ChatGPT**

---

<p align="center">
  <sub>Raspberry Pi Kiosk Dashboard · modular system monitoring</sub>
</p>
