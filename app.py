from PIL import Image, ImageDraw, ImageFont, Image
from datetime import datetime, timezone, timedelta
from weather import fetch_weather, fetch_weather_later
from icon_helper import get_icon_path
from calendar_helper import get_today_events_grouped
from config import API_KEY, CITY, LANG, UNITS
import os
import json
import glob
import requests
import time
import locale
import feedparser
import qrcode
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from PIL import Image
from inky.auto import auto

locale.setlocale(locale.LC_TIME, "de_CH.UTF-8")

def draw_wrapped_text(draw, text, font, max_width, position, line_spacing=5, fill="black"):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        test_width = draw.textbbox((0, 0), test_line, font=font)[2]
        if test_width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    x, y = position
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

def draw_calendar_entry(draw, entry, fonts, position, max_width=360, spacing=5):
    font_bold, font_regular = fonts
    x, y = position

    # Zeit & Farbe bestimmen
    if entry.startswith("Ganztägig"):
        time_part = "Ganztägig"
        desc_part = entry[len("Ganztägig - "):]
        time_color = (255, 140, 0)
    else:
        time_part, desc_part = entry.split(" - ", 1)
        time_color = "black"

    # Uhrzeit zeichnen
    draw.text((x, y), time_part, font=font_bold, fill=time_color)
    time_bbox = draw.textbbox((x, y), time_part, font=font_bold)
    time_width = time_bbox[2] - time_bbox[0]
    text_x = x + time_width + 8  # etwas Abstand

    # Beschreibung umbrechen
    words = desc_part.split()
    line = ""
    lines = []
    for word in words:
        test_line = f"{line} {word}".strip()
        test_bbox = draw.textbbox((0, 0), test_line, font=font_regular)
        test_width = test_bbox[2] - test_bbox[0]
        if test_width + time_width + 8 <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Alle Zeilen der Beschreibung zeichnen
    for i, line in enumerate(lines):
        draw_y = y + i * (font_regular.size + spacing)
        draw.text((text_x, draw_y), line, font=font_regular, fill="black")

    # Gesamthöhe zurückgeben (für y += ...)
    return y + len(lines) * (font_regular.size + spacing)

def draw_temperature_chart(city, api_key, units, lang, target_img, position=(10, 360), max_height=140):
    today = datetime.now(timezone.utc).date()
    cache_filename = f"/tmp/{today.strftime('%Y%m%d')}_forecast.json"

    # Alte Cache-Dateien löschen (älter als 7 Tage)
    try:
        for file in glob.glob("/tmp/*_forecast.json"):
            if os.path.getmtime(file) < time.time() - 7 * 86400:
                os.remove(file)
    except Exception as e:
        print(f"Fehler beim Löschen alter Forecast-Dateien: {e}")

    try:
        if os.path.exists(cache_filename):
            with open(cache_filename, "r") as f:
                data = json.load(f)
        else:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units={units}&lang={lang}"
            res = requests.get(url)
            data = res.json()
            with open(cache_filename, "w") as f:
                json.dump(data, f)

        temps, times = [], []
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            if dt.date() == today:
                temps.append(item["main"]["temp"])
                times.append(dt)

        if not temps:
            return

        fig_height_inches = max_height / 90
        fig, ax = plt.subplots(figsize=(5.8, fig_height_inches), dpi=100)

        ax.xaxis_date()
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # alle 2 Stunden
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

        ax.plot(times, temps, marker="o", color="black", linewidth=5)

        min_temp = min(temps)
        max_temp = max(temps)

        ax.axhline(y=min_temp, linestyle="--", linewidth=4, color="black")
        ax.axhline(y=max_temp, linestyle="--", linewidth=4, color="black")

        ax.text(len(times)-0.5, min_temp + 0.2, f"Min: {min_temp:.1f}°", fontsize=14, color="black")
        ax.text(len(times)-0.5, max_temp + 0.2, f"Max: {max_temp:.1f}°", fontsize=14, color="black")

        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        ax.set_ylabel("°C", fontsize=13)
        ax.set_xlabel("")
        ax.set_title("Temperaturverlauf heute", fontsize=13, pad=8)
        ax.tick_params(axis='x', labelrotation=45, labelsize=12)
        ax.tick_params(axis='y', labelsize=12)

        for spine in ax.spines.values():
            spine.set_visible(False)

        buf = io.BytesIO()
        fig.tight_layout(pad=2.0)
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        chart = Image.open(buf).convert("RGB")
        chart = chart.resize((360, max_height))
        target_img.paste(chart, position)

    except Exception as e:
        print(f"Fehler beim Zeichnen des Temperaturverlaufs: {e}")

BLACK = "black"
BLUE = (0, 0, 255)
ORANGE = (255, 140, 0)

resolution = (800, 480)
img = Image.new("RGB", resolution, color="white")
draw = ImageDraw.Draw(img)

middle_x = resolution[0] // 2
draw.line([(middle_x, 0), (middle_x, resolution[1])], fill="black", width=2)

font_big = ImageFont.truetype("static/fonts/DejaVuSans-Bold.ttf", 42)
font_day = ImageFont.truetype("static/fonts/DejaVuSans.ttf", 20)
font_label = ImageFont.truetype("static/fonts/DejaVuSans-Bold.ttf", 26)
font_value = ImageFont.truetype("static/fonts/DejaVuSans.ttf", 22)

today = datetime.now()
weekday = today.strftime("%A")
day = today.strftime("%d")
month = today.strftime("%B")

draw.text((10, 10), weekday, font=font_big, fill=BLACK)
bbox = draw.textbbox((10, 10), weekday, font=font_big)
text_width = bbox[2] - bbox[0]
x_date = 10 + text_width + 10

draw.text((x_date, 10), day, font=font_day, fill=BLACK)
draw.text((x_date, 35), month, font=font_day, fill=BLACK)

weather_now = fetch_weather()
weather_later = fetch_weather_later()

def paste_png(draw_img, png_path, position, size=(80, 80)):
    try:
        icon = Image.open(png_path).convert("RGBA").resize(size)
        draw_img.paste(icon, position, icon)
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")

draw.text((10, 70), "Wetter Jetzt", font=font_label, fill=BLACK)
paste_png(img, get_icon_path(weather_now['icon']), (10, 110))
draw.text((110, 110), weather_now["description"], font=font_value, fill=BLACK)
draw.text((110, 140), f"{weather_now['temperature']}°", font=font_value, fill=ORANGE)
draw.text((110, 170), f"{weather_now['wind']} Wind", font=font_value, fill=BLUE)
#draw.text((110, 200), f"{weather_now['rain']} Regen", font=font_value, fill=BLUE)

draw.text((10, 220), "Wetter in 6 Stunden", font=font_label, fill=BLACK)
paste_png(img, get_icon_path(weather_later['icon']), (10, 260))
draw.text((110, 260), weather_later["description"], font=font_value, fill=BLACK)
draw.text((110, 290), f"{weather_later['temperature']}°", font=font_value, fill=ORANGE)
draw.text((110, 320), f"{weather_later['wind']} Wind", font=font_value, fill=BLUE)
#draw.text((110, 350), f"{weather_later['rain']} Regen", font=font_value, fill=BLUE)

rss_url = "https://partner-feeds.beta.20min.ch/rss/20minuten/zentralschweiz"
feed = feedparser.parse(rss_url)
first_entry = feed.entries[0]
news_title = first_entry.title

font_news_title = ImageFont.truetype("static/fonts/DejaVuSans-Bold.ttf", 26)
font_news_content = ImageFont.truetype("static/fonts/DejaVuSans.ttf", 20)

news_x = middle_x + 20
news_y = 10

draw.text((news_x, news_y), "News", font=font_news_title, fill="black")

qr = qrcode.QRCode(box_size=2, border=1)
qr.add_data(first_entry.link)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
qr_img = qr_img.resize((70, 70))
qr_position = (news_x, news_y + 40)
img.paste(qr_img, qr_position)

text_offset_x = qr_position[0] + 70
text_offset_y = qr_position[1]
draw_wrapped_text(draw, news_title, font_news_content, max_width=300, position=(text_offset_x, text_offset_y))

# Kalender anzeigen (mehrere Kalender mit Überschriften)
calendar_ids = {
    "Jascha": "primary",
    "Anna": "anna.rueegg34@gmail.com"
}
grouped_events = get_today_events_grouped(calendar_ids)

# Fonts definieren
font_news_time = ImageFont.truetype("static/fonts/DejaVuSans-Bold.ttf", 20)

y = 140
for header, entries in grouped_events:
    draw.text((news_x, y), header, font=font_news_title, fill="black")
    y += 30
    for entry in entries:
        y = draw_calendar_entry(draw, entry, (font_news_time, font_news_content), (news_x, y))
        y += 5  # zusätzlicher Abstand zwischen Einträgen

draw_temperature_chart(CITY, API_KEY, UNITS, LANG, img, position=(10, 360), max_height=120)

now_str = datetime.now().strftime("Stand: %H:%M")
font_small = ImageFont.truetype("static/fonts/DejaVuSans.ttf", 10)

# Textgröße berechnen
bbox = draw.textbbox((0, 0), now_str, font=font_small)
text_width = bbox[2] - bbox[0]

# Position unten rechts (mit 10 px Abstand)
x = resolution[0] - text_width - 10
y = resolution[1] - 20

draw.text((x, y), now_str, font=font_small, fill="black")

img.save("dashboard_simulation.png")

try:
    inky = auto(ask_user=True, verbose=True)
    resized = img.resize(inky.resolution)
    inky.set_image(resized)
    inky.show()
except Exception as e:
    print(f"Fehler beim Anzeigen auf dem Inky Display: {e}")
