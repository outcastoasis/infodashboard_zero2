#!/bin/bash
set -e

echo "Starte Setup fuer Raspberry Pi Zero 2 W..."

sudo apt update
sudo apt install -y cron git python3 python3-pip python3-venv
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev libopenjp2-7 libtiff-dev

sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --prefer-binary

if [ ! -d inky ]; then
  git clone https://github.com/pimoroni/inky
fi

cd inky
yes | ./install.sh
cd ..

mkdir -p log

echo "Setup abgeschlossen."
echo "Naechster Schritt: calendars.local.json mit deinen iCal-Links erstellen."
