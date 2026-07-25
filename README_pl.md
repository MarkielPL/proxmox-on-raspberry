- [ ] tłumaczenie AI - sprawdzić!

# PXVIRT Proxmox fork proces instalacji na Raspberry Pi <br />




Zobacz zawarty skrypt do automatycznego uruchamiania wszystkich zadań przed instalacją. <br />
Proxmox VE nie jest jeszcze oficjalnie dostępny dla architektury ARM na stronie Proxmox. <br />
Istnieje jednak wiele forków tego projektu, które już działają świetnie. <br />
Skrypt i README bazują na instrukcjach dla forku pxvirt: <br />
https://docs.pxvirt.lierfang.com/en/installfromdebian.html <br />
Może być używany z Raspberry Pi 3B lub nowszym (3B+, Raspberry 4, 5, 500 itd) <br /> <br />
Chociaż będzie działać na urządzeniach z zaledwie 1GB RAM, zaleca się Raspberry z co najmniej 4GB pamięci RAM. <br />
Działa z Debian 12 Bookworm i Debian 13 Trixie. <br />
Uwaga - jeśli najpierw zainstaluje się Debian 12 na Raspberry, otrzymasz Proxmox 8, <br />
ale jeśli zainstaluje się Debian 13 - otrzymasz Proxmox 9. <br /> <br />

## Proces nagrywania Raspberry Pi: <br />
Pobierz Raspberry Pi Imager stąd: https://www.raspberrypi.com/software/ <br /> 
Podłącz Raspberry Pi do sieci PRZEWODOWO! <br />
(chociaż Pi ma moduł bezprzewodowy - byłoby trudno uruchomić go z Proxmoxem). <br />
Nagrywaj kartę MicroSD lub dysk SSD wybierając Debian 12 (Bookworm) lub Debian 13 (Trixie) - sugeruję wybrać ten ostatni. <br />
Włóż kartę MicroSD lub SSD i uruchom Raspberry Pi. <br />
Postępuj zgodnie z procesem na ekranie, aby ukończyć instalację Debian. <br /> <br />

## Proces przygotowania Raspberry Pi: <br />
Jeśli uruchomisz system operacyjny na MicroSD, unikaj korzystania z wymiany, ponieważ nie tylko jest wolna <br />
ale szybko zniszczy twoją kartę MicroSD. <br />
Możesz uruchomić polecenie `sudo swapoff -a`, sprawdzić dowolne wpisy dotyczące wymiany w `/etc/fstab` i ponownie uruchomić system. <br />
Proxmox wymaga hasła roota po zalogowaniu się do niego, a domyślnie Raspberry nie ma skonfigurowanego hasła dla użytkownika root. <br />
Musisz go utworzyć, uruchamiając `sudo passwd root` i wpisując hasło dwa razy, aby je skonfigurować. <br />
Sprawdź bieżące interfejsy poleceniem `ip address`, zobacz, czy masz prawidłowy adres IP i na jakim interfejsie. <br />
Sprawdź bieżące wpisy w `/etc/hosts`, uruchamiając polecenie `cat /etc/hosts`. <br />

## Teraz uruchom zawarty skrypt przygotowania pxvirt <br />
Po prostu sklonuj skrypt za pomocą git lub nawet skopiuj stąd i pamiętaj o `chmod +x`. <br />
Uruchom skrypt z uprawnieniami sudo - więc `sudo ./pxvirtpreps.sh` <br />
Po zakończeniu procesu - uruchom ponownie Pi. <br />
Sprawdź ponownie interfejsy sieciowe za pomocą `cat /etc/network/interfaces` <br />
Powinieneś teraz zobaczyć utworzony most sieciowy linux vmbr0 i powinien mieć przypisany adres IP, coś w rodzaju: <br />
```bash
auto eth0
iface eth0 inet manual

auto vmbr0
iface vmbr0 inet manual
    address 192.168.1.59/24
    gateway 192.168.1.1
    bridge-ports eth0
    bridge-stp off
    bridge-fd 0
```
Możesz również uruchomić `cat /etc/apt/sources.list.d/pxvirt-sources.list` i powinieneś zobaczyć tam tę linię: <br />
`deb  https://mirrors.lierfang.com/pxcloud/pxvirt $VERSION_CODENAME main` <br />
gdzie `$VERSION_CODENAME` zostanie zastąpiony bookworm lub trixie w zależności od wersji debiana, którą uruchamiasz. <br />
Sprawdź ponownie plik hosts, uruchamiając polecenie `cat /etc/hosts` i zobacz, czy masz IP skierowany do hosta raspberrypi <br />

## Proces instalacji PXVIRT <br />
Wystarczy uruchomić `apt update`, a następnie: <br />
`apt install proxmox-ve pve-manager qemu-server pve-cluster -y` zgodnie z instrukcją na stronie pxvirt. <br />
Ten proces może potrwać ponad 10 minut i możesz zobaczyć, że ekran włącza się i wyłącza. <br />
Po ukończeniu - powinieneś mieć dostęp do Proxmox z dowolnego urządzenia w sieci, przechodząc do: <br />
`https://<vmbr0_ip_address>:8006` <br />

## Montowanie lokalizacji NAS do Raspberry <br />
Nie jest to związane z procesem opisanym powyżej, ale jeśli chcesz zamontować NAS do Raspberry, wystarczy <br />
utworzyć folder takim jak `mkdir -p /mnt/marek` i uruchom to: <br />
`mount -t cifs -o username=marek //192.168.1.225/Shared /mnt/marek/`
