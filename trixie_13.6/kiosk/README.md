# Raspberry Pi Kiosk Dashboard

> **Modularny dashboard systemowy dla Raspberry Pi 5**, uruchamiany w trybie kiosk na terminalu tekstowym.
>
> Projekt został zaprojektowany jako lekki, modularny i odporny na błędy interfejs monitorujący system Raspberry Pi, Proxmox VE, Pi-hole, pamięć masową, sieć oraz układ chłodzenia.
---
<img width="1182" height="638" alt="{EFF87572-FE4F-4018-88D6-FE30679045D5}" src="https://github.com/user-attachments/assets/e8829688-8bd1-4a61-838f-659f1d6a04b7" />

---

## 📌 Status projektu

**Wersja:** `0.2.2` -> `0.2.3`
> [!NOTE] 
> Sprawdzenie czy migracja z Rich na Textual ma sens. Wykonanie testów. opracownaie wyników. Utworzenie pliku z historią wersji. Wprowadzane zasady:`  

`Zasada 1 - UI nigdy nie czyta systemu;`    
```
collector
   ↓
DashboardState
   ↓
panel/widget
```
`Zasada 2 - UI refresh nie powoduje collector refresh`  
 ```
 10 FPS UI ≠ 10 odczytów CPU/s ≠ 10 requestów Proxmox/s
```
`Zasada 3 - Backend nie wie, jaki framework UI go wykorzystuje`   
```
collectors
models
cache
manager
       │
       ▼
DashboardState
       │
       ├── Rich
       ├── Textual
       └── potencjalnie inne UI
```
 

- [ ] 1.1. Przejrzeć `models.py`;  
- [ ] 1.2. Ustalić ostateczny kontrakt `DashboardState`;
- [ ] 1.3. Przejrzeć wszystkie collectory;
- [ ] 1.4. Ujednolicić sposób zwracania danych przez collectory;
- [ ] 1.5. Przejrzeć `collector_manager.py`;
- [ ] 1.6. Usunąć zależności managera od warstwy UI;
- [ ] 1.7. Przejrzeć `services/cache.py`;
- [ ] 1.8. Ustalić zachowanie przy błędach collectorów;
- [ ] 1.9. Ustalić jednoznaczny przepływ.

Warstwa danych musi działać bez wiedzy o tym, czy UI jest Rich, Textual, GTK czy Qt.
 
    UI refresh  
        │   
        │ np. 0.2 s 
        ▼   
    DashboardState  
        │   
        ├── CPU ────────────── aktualizuj co 1 s    
        ├── Network ────────── aktualizuj co 1 s    
        ├── RAM ────────────── aktualizuj co 2 s    
        ├── Fan ────────────── aktualizuj co 2 s    
        ├── Temperature ────── aktualizuj co 5 s    
        ├── NVMe ───────────── aktualizuj co 5 s   
        ├── Proxmox ────────── aktualizuj co 5 s   
        ├── Pi-hole ────────── aktualizuj co 10 s  
        ├── System ─────────── aktualizuj co 5 s   
        └── Storage ────────── aktualizuj co 60 s 

- [ ] 2.1. Ustalić częstotliwość każdego collectora;
- [ ] 2.2. Wprowadzić jeden spójny mechanizm `needs_update()`;
- [ ] 2.3. Sprawdzić, czy żaden collector nie jest wywoływany poza managerem;
- [ ] 2.4. Sprawdzić, czy UI nie wykonuje odczytów systemowych;
- [ ] 2.5. Sprawdzić zachowanie przy błędzie;
- [ ] 2.6. Dodać timestamp ostatniej aktualizacji danych.

Sprawdzenie obciązeniua
- [ ] 3.1. Zmierzyć dashboard + Rich;
- [ ] 3.2. Zmierzyć idle dashboard;
- [ ] 3.3. Zmierzyć przy intensywnym odświeżaniu;
- [ ] 3.4. Zapisać wynik jako baseline;
- [ ] 3.5. Po migracji do Textual powtórzyć pomiar;
- [ ] 3.6. Porównać CPU/RAM/temperaturę;
- [ ] 3.7. Oddzielić formatowanie danych od renderowania;
- [ ] 3.8  Upewnić się, że `panels.py` nie zawiera logiki systemowej;

Wynonanie testów równoległych:  
```
backend 
   │    
   ├── Rich 
   │    
   └── Textual  
```
Textual zwiększył RAM o X MB i CPU o Y%.

### Natępnie po udanej migracji:
- [ ] Sprawdzić obsługę symboli Nerd Font;
- [ ] Proxmox - osobny etap, ponieważ ważnym źródłem danych, ale nie chcemy go odpytywać zbyt często:
    - 4.1. Ustalić dokładne dane pobierane z PVE;
    - 4.2. Ustalić interwał;
    - 4.3. Cache danych Proxmox;
    - 4.4. Status VM;
    - 4.5. CPU;
    - 4.6. RAM;
    - 4.7. uptime;
    - 4.8. obsługa niedostępności API;
    - 4.9. nie blokować UI podczas API request.
```
    PROXMOX
    ────────────────
    Node       online
    CPU        xx%
    Memory     xx%
    Uptime     xxd
    ────────────────
    VM 100     ●
    VM 101     ●
    VM 102     ○
```
- [ ] Analogicznie Pi-hole:
    - 5.1. status Pi-hole;
    - 5.2. queries;
    - 5.3. blocked;
    - 5.4. percentage blocked;
    - 5.5. uptime/status;
    - 5.6. błędy API;
    - 5.7. interwał np. 10 s;
    - 5.8. brak blokowania głównej pętli.

- [ ] Sprawdzić monitoring sprzętu - collectory mają czytać dane, UI ma ich nie czytać:
    - 6.1. CPU;
    - 6.2. RAM/SWAP;
    - 6.3. CPU temperature;
    - 6.4. NVMe temperature;
    - 6.5. RP1;
    - 6.6. fan RPM;
    - 6.7. PWM;
    - 6.8. storage;
    - 6.9. network;

- [ ] Poprawić alerty, docelowo:    
    ```
    Collector   
       ↓    
    DashboardState  
       ↓    
    Alert Engine    
       ↓    
    ┌─────────────┬─────────────┬────────────┐  
    │ UI warning  │ popup       │ log        │  
    └─────────────┴─────────────┴────────────┘  
    ```

- [ ] Wykonaćtesty i poprawić dokumentację:
    - 7.1. test CPU;
    - 7.2. test RAM;
    - 7.3. test temperature;
    - 7.4. test fan;
    - 7.5. test NVMe;
    - 7.6. test storage;
    - 7.7. test network;
    - 7.8. test Proxmox;
    - 7.9. test Pi-hole;
    - 7.10. test cache;
    - 7.11. test manager;
    - 7.12. test błędów.

```
FAZA A — FUNDAMENT
────────────────────────────────────
1. Stabilizacja architektury
2. Twarde interwały collectorów
3. Cache
4. Pomiar obciążenia
             │
             ▼
FAZA B — ODSEPAROWANIE UI
────────────────────────────────────
5. Oddzielenie UI od backendu
             │
             ▼
FAZA C — DECYZJA
────────────────────────────────────
6. Rich vs Textual
             │
       ┌─────┴─────┐
       │           │
     Rich       Textual
       │           │
       │           ▼
       │     nowy frontend
       │           │
       └─────┬─────┘
             ▼
FAZA D — FUNKCJE
────────────────────────────────────
7. Typografia/assets
8. Proxmox
9. Pi-hole
10. Hardware monitoring
11. Alerts
12. Logging
             │
             ▼
FAZA E — HARDENING
────────────────────────────────────
13. systemd/tty3
14. security
15. config
16. tests
             │
             ▼
FAZA F — DOKUMENTACJA
────────────────────────────────────
17. README
18. finalizacja
```


**Platforma docelowa:** Raspberry Pi 5 8 GB  
**System:** Debian GNU/Linux 13 (Trixie)  
**Kernel:** Linux 6.18.x / aarch64  
**Virtualizacja:** Proxmox VE 9  
**Interfejs:** terminal / Rich  -> Textual  
**Tryb pracy:** kiosk / daemon  
**Docelowy ekran:** mały ekran dotykowy

Projekt jest rozwijany etapami. Obecna architektura stanowi bazę pod dalszą rozbudowę bez konieczności przebudowy całego programu.
```

                    RPi5                │       RPi 5 8 GB
                     │                  │       │
              Debian Trixie             │       ├── Debian 13 Trixie
                     │                  │       │
          ┌──────────┴──────────┐       │       ├── Proxmox VE 9
          │                     │       │       │   ├── Pi-hole
       Proxmox                Kiosk     │       │   ├── Zigbee / SmartHome gateway
          │                     │       │       │   └── 1 VM free slot
    ┌─────┴─────┐           Textual     │       │
    │           │              │        │       └── Kiosk Dashboard
 Pi-hole      Zigbee          tty3      │           └── process on host
                                        │               └── tty3
```


---

# 📁 Project tree
```
kiosk/        
│     
├── dashboard.py              ← entry point     
├── config.py                 ← konfiguracja  
├── models.py                 ← dane  
├── requirements.txt  
│     
├── collectors/       
│   ├── cpu.py                    
│   ├── memory.py             
│   ├── network.py                
│   ├── storage.py                
│   ├── sensors.py                
│   ├── fan.py                
│   ├── nvme.py               
│   ├── proxmox.py                
│   ├── pihole.py             
│   └── system.py             
│             
├── services/             
│   ├── cache.py              
│   └── collector_manager.py              
│             
├── ui/               
│   ├── app.py                
│   │             
│   ├── screens/              
│   │   └── dashboard.py              
│   │             
│   ├── widgets/              
│   │   ├── cpu.py                
│   │   ├── memory.py             
│   │   ├── network.py                
│   │   ├── temperature.py                
│   │   ├── fan.py                
│   │   ├── storage.py                
│   │   ├── nvme.py               
│   │   ├── pihole.py             
│   │   ├── proxmox.py                
│   │   └── system.py             
│   │             
│   └── styles/               
│       └── dashboard.tcss                
│             
├── assets/               
│   ├── fonts/                
│   ├── images/               
│   └── icons/                
│             
├── logs/             
│   └── dashboard.log             
│             
└── tests/                
    ├── collectors/               
    ├── services/             
    └── ui/               
```
---

# 6. 📦 Migration stages 🛡️
```
ETAP 1  
requirements.txt    
    ↓   
ETAP 2  
config.py   
    ↓   
ETAP 3  
models.py   
    ↓   
ETAP 4  
collectors/ 
    ↓   
ETAP 5  
services/cache.py   
    ↓   
ETAP 6  
services/collector_manager.py   
    ↓   
ETAP 7  
measurement CPU/RAM  
    ↓   
ETAP 8  
ui/app.py   
    ↓   
ETAP 9  
Textual widgets
    ↓   
ETAP 10 
layout + TCSS   
    ↓   
ETAP 11 
test Textual on tty3    
    ↓   
ETAP 13 
removing panels.py 
    ↓   
ETAP 14 
font/assets 
    ↓   
ETAP 15 
alerts  
    ↓   
ETAP 16 
tests   
    ↓   
ETAP 17 
README  
```