#!/bin/bash

# chmod +x setup.sh
# ./setup.sh 
echo "Starte Setup für Raspberry Pi Zero W (optimiert)..."

# 1. System aktualisieren
sudo apt update && sudo apt upgrade -y

# 2. SPI aktivieren (Inky nutzt SPI und I2C)
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# 3. Cron installieren (falls noch nicht vorhanden)
sudo apt install -y cron

# 4. Python & Paketmanager installieren
sudo apt install -y python3 python3-pip python3-venv git

# 5. Systembibliotheken für Pillow, numpy, matplotlib
sudo apt install -y \
  libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev \
  libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
  libopenjp2-7 libtiff-dev libatlas-base-dev

# 6. Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# 7. Inky manuell installieren (lite) mit automatischer Bestätigung
git clone https://github.com/pimoroni/inky
cd inky
yes | ./install.sh
cd ..

# 8. Abhängigkeiten installieren (leichtgewichtiger Matplotlib)
pip install --upgrade pip
pip install -r requirements.txt --prefer-binary

# 9. Logverzeichnis erstellen
mkdir -p log

echo "Setup abgeschlossen. Das Dashboard wird nun alle 15 Minuten aktualisiert."
