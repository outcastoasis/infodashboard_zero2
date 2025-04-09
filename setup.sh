#!/bin/bash

# chmod +x setup.sh
# ./setup.sh 
echo "Starte Setup..."

# 1. System aktualisieren
sudo apt update && sudo apt upgrade -y

# 2. SPI aktivieren (Inky nutzt SPI)
sudo raspi-config nonint do_spi 0

# 3. Cron installieren (falls noch nicht vorhanden)
sudo apt install -y cron

# 4. Python & Paketmanager installieren
sudo apt install -y python3 python3-pip python3-pil python3-numpy

# 5. Systembibliotheken
sudo apt install -y libopenjp2-7 libtiff5 git

# 6. Inky-Bibliothek + Abhängigkeiten
curl https://get.pimoroni.com/inky | bash

# 7. Dein Projektverzeichnis vorausgesetzt im gleichen Ordner wie setup.sh
cd "$(dirname "$0")"

# 8. Python-Abhängigkeiten installieren
pip3 install -r requirements.txt

# 9. Logverzeichnis erstellen
mkdir -p log

# 10. Cronjob einrichten
SCRIPT_PATH="$(pwd)/app.py"
LOG_PATH="$(pwd)/log/inky.log"

# Existierenden Job entfernen, falls vorhanden
(crontab -l | grep -v "$SCRIPT_PATH") 2>/dev/null > tempcron

# Neuen Job hinzufügen (alle 15 Minuten zur Viertelstunde)
echo "15,30,45,0 * * * * /usr/bin/python3 $SCRIPT_PATH >> $LOG_PATH 2>&1" >> tempcron
crontab tempcron
rm tempcron

echo "Setup abgeschlossen. Das Dashboard wird nun alle 15 Minuten aktualisiert."
