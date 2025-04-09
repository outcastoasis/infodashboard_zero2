#!/bin/bash

# chmod +x setup.sh
# ./setup.sh 
echo "🔧 Starte Setup für Raspberry Pi Zero W (optimiert)..."

# 1. System aktualisieren
sudo apt update && sudo apt upgrade -y

# 2. SPI aktivieren (Inky nutzt SPI)
sudo raspi-config nonint do_spi 0

# 3. Cron installieren (falls noch nicht vorhanden)
sudo apt install -y cron

# 4. Python & Paketmanager installieren
sudo apt install -y python3 python3-pip python3-venv git

# 5. Systembibliotheken für Pillow, numpy, matplotlib
sudo apt install -y \
  libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev \
  libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
  libopenjp2-7 libtiff5 libatlas-base-dev

# 6. Inky manuell installieren (lite)
git clone https://github.com/pimoroni/inky
cd inky
sudo ./install.sh --display "impression7" --lite
cd ..
rm -rf inky

# 7. Projektverzeichnis setzen
cd "$(dirname "$0")"

# 8. Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# 9. Abhängigkeiten installieren (leichtgewichtiger Matplotlib)
pip install --upgrade pip
pip install -r requirements.txt --prefer-binary
pip install matplotlib==3.3.4

# 10. Logverzeichnis erstellen
mkdir -p log

# 11. Cronjob einrichten
SCRIPT_PATH="$(pwd)/app.py"
LOG_PATH="$(pwd)/log/inky.log"
PYTHON_PATH="$(pwd)/venv/bin/python"

# Existierenden Job entfernen, falls vorhanden
(crontab -l | grep -v "$SCRIPT_PATH") 2>/dev/null > tempcron

# Neuen Job hinzufügen (alle 15 Minuten zur Viertelstunde)
echo "15,30,45,0 * * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1" >> tempcron
crontab tempcron
rm tempcron

echo "✅ Setup abgeschlossen. Das Dashboard wird nun alle 15 Minuten aktualisiert."
