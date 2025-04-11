# 🖥️ Inky Infodashboard

Ein Infodisplay für das Inky Impression 7.3" Display auf dem Raspberry Pi Zero 2 W.  
Zeigt Wetter, News, Kalendertermine (auch ganztägige), QR-Codes sowie ein Temperaturdiagramm an – optimiert für stromsparende E-Ink-Anzeige.

---

## ⚙️ Features

- Lokale Wetterdaten von OpenWeatherMap
- Automatische Vorschau der nächsten 6 Stunden
- RSS-News (z. B. 20min.ch) mit QR-Code
- Google-Kalender-Integration für mehrere Konten
- Temperaturverlauf des Tages mit Min-/Max-Markierung (Matplotlib)
- Viertelstündliches Update via Cronjob

---

## ⚙️ Konfiguration

Der Standort der Wetterdaten kann in der config.py geändert werden.

---

## 📦 Projektstruktur

```text
Inky_Infodashboard/
├── app.py                  # Hauptprogramm (zeichnet das Dashboard)
├── weather.py              # Wetterdaten (OpenWeatherMap)
├── calendar_helper.py      # Google-Kalender-Integration
├── icon_helper.py          # Pfade für Wetter-Icons
├── config.py               # API-Einstellungen aus .env
├── requirements.txt        # Python-Abhängigkeiten
├── static/                 # Fonts
├── icons/                  # Lokale SVG-Wettersymbole
├── .env                    # API Key für OpenWeatherMap (nicht in Git!)
├── credentials.json        # Google OAuth
├── token.json              # Zwischengespeicherte Tokens
├── dashboard_simulation.png# Optional: Vorschau vom generierten Bild
├── setup.sh                # Einmaliges Setup-Skript
└── README.md               # Diese Datei
```

---

## 🔁 Automatische Anzeige

Das Skript `setup.sh` installiert alle wichtigen Pakete und richtet einen **Cronjob** ein, der `app.py` automatisch um :15 und :45 aufruft und das E-Ink Display aktualisiert.

---

## 🚀 Installation

```bash
git clone https://github.com/outcastoasis/infodashboard_zero2.git
cd infodashboard_zero2
chmod +x setup.sh
./setup.sh
```

---

## 🌐 APIs & Zugang

- `.env` muss folgendes enthalten:

```env
API_KEY=dein_openweathermap_api_key
```

- Für Google Kalender muss `credentials.json` vorhanden sein.
- Gehe zu Google Cloud Console
- Aktiviere die Google Calendar API
- Erstelle Anmeldedaten für eine "Desktop App"
- Lade die credentials.json herunter und lege sie ins Projektverzeichnis
- Beim ersten Start von app.py wirst du zur Authentifizierung im Browser weitergeleitet – dabei wird automatisch eine token.json erstellt.

---

## 🖼️ Beispielanzeige

![Beispiel](assets/dashboard_simulation_git.png)

---

## 🧪 Manuelles Testen

```bash
python3 app.py
```

---

## 📅 Cronjob prüfen

```bash
crontab -l
```

---
