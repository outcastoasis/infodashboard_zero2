# Inky Infodashboard

Ein reduziertes Infodisplay fuer ein Pimoroni Inky Impression am Raspberry Pi Zero 2 W.

Der Fokus liegt auf:

- Wetter jetzt und in 6 Stunden
- Temperaturverlauf fuer den aktuellen Tag
- Kalendertermine von iCal/ICS-Links
- lokaler PNG-Vorschau ohne Inky-Display

20min-News, QR-Codes und Google-OAuth wurden entfernt. Kalender werden nur lesend ueber iCal-Links geladen.

## Dateien

```text
app.py                    Einstiegspunkt
config.py                 liest .env und Kalender-Konfiguration
calendar_ical.py          laedt iCal/ICS-Kalender
weather.py                laedt OpenWeatherMap Forecast
renderer.py               zeichnet das Dashboard mit Pillow
display.py                speichert PNG und aktualisiert Inky
calendars.example.json    Vorlage fuer Kalenderlinks
requirements.txt          Python-Abhaengigkeiten
setup.sh                  Raspberry-Pi-Setup
```

## Konfiguration

`.env`:

```env
API_KEY=dein_openweathermap_api_key
WEATHER_CITY=Menzingen,CH
DASHBOARD_TIMEZONE=Europe/Zurich
```

Kalender lokal anlegen:

```bash
cp calendars.example.json calendars.local.json
nano calendars.local.json
```

`calendars.local.json`:

```json
[
  {
    "name": "Jascha",
    "url": "https://calendar.google.com/calendar/ical/.../private-.../basic.ics"
  }
]
```

Diese Datei wird von Git ignoriert, weil die privaten iCal-Links wie Geheimnisse behandelt werden sollten.

## iCal-Link In Google Calendar Finden

1. Google Calendar im Browser oeffnen.
2. Beim gewuenschten Kalender: Einstellungen und Freigabe.
3. Abschnitt "Kalender integrieren".
4. "Geheime Adresse im iCal-Format" kopieren.
5. Link in `calendars.local.json` einfuegen.

Wenn die geheime iCal-Adresse nicht sichtbar ist, kann sie bei Google-Workspace-Konten durch Admin-Einstellungen deaktiviert sein.

## Lokal Testen

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py --no-display
```

Danach liegt die Vorschau in `dashboard_simulation.png`.

Unter Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py --no-display
```

## Raspberry Pi

```bash
cd ~/Inky_Infodashboard
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Die Display-Ausgabe nutzt weiterhin Pimoroni Inky:

```python
from inky.auto import auto
display = auto()
display.set_image(image)
display.show()
```

## Cronjob

Beispiel fuer Updates um :15 und :45:

```cron
15,45 * * * * /bin/bash -l -c 'cd /home/pi/Inky_Infodashboard && source venv/bin/activate && python app.py >> log/inky.log 2>&1'
```

