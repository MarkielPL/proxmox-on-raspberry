
[debian template](https://github.com/DanieleMassa/proxmoxOnRPI5)


[Pi-Hole web](https://github.com/pi-hole/pi-hole)

[Display Control Library](https://github.com/tomba/kmsxx/)


required dependencies:

```bash
sudo apt update && sudo apt install -y \
    build-essential \
    pkg-config \
    cmake \
    meson \
    ninja-build \
    libdrm-dev \
    libevdev-dev \
    python3-dev \
    python3-venv \
    python3-pip \
    python3-setuptools \
    python3-wheel
```

- ## Displaying BTOP in kiosk mode after startup:


```bash
sudo nano /etc/systemd/system/btop-display.service
```


Content:

>[Unit]
>
>Description=btop system monitor on primary display
>
>After=systemd-user-sessions.service getty@tty1.service
>
>Conflicts=getty@tty1.service
>
>[Service]
>
>Type=simple
>
>User=[YOURUSER] <----------- change
>
>TTYPath=/dev/tty1
>
>StandardInput=tty
>
>StandardOutput=tty
>
>StandardError=journal
>
>ExecStart=/usr/bin/btop
>
>Restart=always
>RestartSec=2
>
>[Install]
>
>WantedBy=multi-user.target

Next:
```bash
sudo systemctl daemon-reload
sudo systemctl enable btop-display.service
sudo systemctl start btop-display.service
systemctl status btop-display.service
```

<details>
<summary><h3>Graphical interface with KMS++</h3></summary>
> ⚠️ Section under construction

- [ ] switch to TT2 and disable login

      sudo systemctl disable --now getty@tty2.service

      systemd
        │
        ▼
      btop-display.service
        │
        ▼
      /dev/tty2
        │
        ▼
      HDMI-A-1
    
- [ ] write your own C++ program using kms++;
- [ ] draw directly into framebuffers, example:

      CPU ─────────────── 37%
      RAM ─────────────── 42%
      TEMP ────────────── 51°C

      NETWORK
      ↓ 125 Mbps
      ↑ 24 Mbps

      PROCESSES
      ...

</details>

- ## Touchscreen blanking

test:
```bash
sudo sh -c 'TERM=linux setterm --blank 1 --powerdown 0 > /dev/tty1'
```
daemon

```bash
sudo nano /etc/systemd/system/console-blank.service
```
content:
> [Unit]
>
> Description=Configure Linux console screen > blanking
>
> After=btop-display.service
>
> Wants=btop-display.service
> 
> [Service]
>
> Type=oneshot
>
> ExecStart=/bin/sh -c 'TERM=linux /usr/bin/setterm > --blank 1 --powerdown 0 > /dev/tty1'
>
> RemainAfterExit=yes
> 
> [Install]
>
> WantedBy=multi-user.target

- ## Wake up

```bash
 sudo nano /etc/systemd/system/touch-wakeup.service
```

content:
> [Unit]
>
>Description=Touchscreen display wakeup daemon
>
>After=systemd-udev-settle.service
>
>After=btop-display.service
>
>Wants=btop-display.service
>
>[Service]
>Type=simple
>
>ExecStart=/usr/local/sbin/touch-wakeup.sh
>
>Restart=always
>RestartSec=2
>
>StandardOutput=journal
>
>StandardError=journal
>
>[Install]
>
>WantedBy=multi-user.target


```bash
sudo systemctl daemon-reload
sudo systemctl enable touch-wakeup.service
sudo systemctl start touch-wakeup.service
sudo systemctl status touch-wakeup.service
```

## autologowanie na tty3

```
sudo nano /etc/systemd/system/switch-to-tty3.service
```

content:

>[Unit]
>
>Description=Force switch to TTY3 on boot
>
>After=getty.target systemd-user-sessions.service
>
>$# Jeśli używasz menedżera logowania (GDM, LightDM, SDDM), dodaj też:
>
>$# After=display-manager.service
>
>
>
>[Service]
>
>Type=oneshot
>
>ExecStart=/usr/bin/chvt 3
>
>RemainAfterExit=yes
>
>
>
>[Install]
>
>WantedBy=multi-user.target
>
>WantedBy=graphical.target


sudo systemctl enable switch-to-tty3.service
