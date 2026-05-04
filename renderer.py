from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from calendar_ical import CalendarEvent, CalendarGroup
from config import BASE_DIR
from icon_helper import get_icon_path
from weather import WeatherData, WeatherPoint


BLACK = "black"
BLUE = (0, 80, 180)
ORANGE = (235, 120, 0)
GRAY = (90, 90, 90)
LIGHT_GRAY = BLACK

FONT_DIR = BASE_DIR / "static" / "fonts"
WEEKDAYS_DE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


class Fonts:
    title = _font("DejaVuSans-Bold.ttf", 42)
    subtitle = _font("DejaVuSans.ttf", 20)
    section = _font("DejaVuSans-Bold.ttf", 26)
    panel_title = _font("DejaVuSans-Bold.ttf", 24)
    body = _font("DejaVuSans.ttf", 22)
    body_bold = _font("DejaVuSans-Bold.ttf", 21)
    event_time = _font("DejaVuSans-Bold.ttf", 18)
    small = _font("DejaVuSans.ttf", 14)
    tiny = _font("DejaVuSans.ttf", 11)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int = 2,
    fill=BLACK,
    line_spacing: int = 4,
) -> int:
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if _text_width(draw, candidate, font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    lines = lines[:max_lines]
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        while lines[-1] and _text_width(draw, lines[-1] + "...", font) > max_width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] += "..."

    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line, font=font)
        y += box[3] - box[1] + line_spacing
    return y


def _draw_icon(image: Image.Image, icon_code: str, xy: tuple[int, int], size: int) -> None:
    try:
        icon = Image.open(get_icon_path(icon_code)).convert("RGBA").resize((size, size))
        image.paste(icon, xy, icon)
    except Exception as exc:
        print(f"Fehler beim Laden des Icons: {exc}")


def _format_temp(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f} °C"


def _format_wind(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f} km/h"


def _draw_weather_point(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    title: str,
    point: WeatherPoint,
    x: int,
    y: int,
    width: int | None = None,
) -> int:
    draw.text((x, y), title, font=Fonts.section, fill=BLACK)
    y += 34
    _draw_icon(image, point.icon, (x, y + 2), 58)
    description_width = (width - 78) if width else 290
    _draw_wrapped(draw, point.description, (x + 74, y), Fonts.body, description_width, max_lines=1)
    draw.text((x + 74, y + 30), _format_temp(point.temperature), font=Fonts.body_bold, fill=ORANGE)
    draw.text((x + 192, y + 30), _format_wind(point.wind), font=Fonts.body, fill=BLUE)
    return y + 76


def _draw_weather_section(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    weather: WeatherData,
    x: int,
    y: int,
    width: int,
    max_y: int,
) -> None:
    y = _draw_weather_point(image, draw, "Jetzt", weather.now, x, y, width)
    y = _draw_weather_point(image, draw, "In 6 Stunden", weather.later, x, y + 8, width)
    chart_y = y + 8
    chart_height = max(86, max_y - chart_y - 28)
    _draw_temperature_strip(draw, weather, x, chart_y, width, chart_height)


def _draw_temperature_strip(
    draw: ImageDraw.ImageDraw,
    weather: WeatherData,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    draw.text((x, y), weather.temperature_title, font=Fonts.section, fill=BLACK)
    y += 34
    box = (x, y, x + width, y + height)
    draw.rectangle(box, outline=LIGHT_GRAY, width=2)

    points = weather.todays_temperatures
    if len(points) < 2:
        message = "Keine Wetterdaten geladen" if weather.error else "Zu wenig Datenpunkte"
        draw.text((x + 12, y + 18), message, font=Fonts.small, fill=BLACK)
        return

    temperatures = [temperature for _, temperature in points]
    min_temp = min(temperatures)
    max_temp = max(temperatures)
    span = max(max_temp - min_temp, 1)

    coords = []
    for index, (_, temperature) in enumerate(points):
        px = x + 14 + round(index * (width - 28) / (len(points) - 1))
        py = y + height - 32 - round((temperature - min_temp) * (height - 56) / span)
        coords.append((px, py))

    draw.line(coords, fill=BLACK, width=4)
    for px, py in coords:
        draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=BLACK)

    draw.text((x + 10, y + 7), f"Min {_format_temp(min_temp)}", font=Fonts.small, fill=BLACK)
    draw.text((x + width - 124, y + 7), f"Max {_format_temp(max_temp)}", font=Fonts.small, fill=BLACK)
    first_time = points[0][0].strftime("%H:%M")
    last_time = points[-1][0].strftime("%H:%M")
    draw.text((x + 12, y + height - 21), first_time, font=Fonts.tiny, fill=BLACK)
    draw.text((x + width - _text_width(draw, last_time, Fonts.tiny) - 12, y + height - 21), last_time, font=Fonts.tiny, fill=BLACK)


def _event_time(event: CalendarEvent, timezone: ZoneInfo) -> str:
    if event.all_day:
        return "Ganztägig"
    start = event.start
    if isinstance(start, datetime):
        return start.astimezone(timezone).strftime("%H:%M")
    return "Ganztägig"


def _draw_event(
    draw: ImageDraw.ImageDraw,
    event: CalendarEvent,
    timezone: ZoneInfo,
    x: int,
    y: int,
    width: int,
) -> int:
    time_text = _event_time(event, timezone)
    time_width = 116
    color = ORANGE if event.all_day else BLACK
    time_font = Fonts.event_time if event.all_day else Fonts.body_bold
    draw.text((x, y + (2 if event.all_day else 0)), time_text, font=time_font, fill=color)
    return _draw_wrapped(
        draw,
        event.title,
        (x + time_width, y),
        Fonts.body,
        max_width=width - time_width,
        max_lines=2,
        fill=BLACK,
    ) + 10


def _draw_calendar_groups(
    draw: ImageDraw.ImageDraw,
    groups: list[CalendarGroup],
    timezone: ZoneInfo,
    x: int,
    y: int,
    width: int,
    max_y: int,
) -> None:
    if not groups:
        draw.text((x, y), "Keine Kalender konfiguriert", font=Fonts.body, fill=BLACK)
        return

    visible_events = 0
    for group in groups:
        if y > max_y - 30:
            break
        draw.text((x, y), group.name, font=Fonts.body_bold, fill=BLACK)
        y += 30

        if group.error:
            y = _draw_wrapped(draw, group.error, (x, y), Fonts.small, width, max_lines=2, fill=BLACK)
            y += 8
            continue

        if not group.events:
            draw.text((x, y), "Keine Termine", font=Fonts.small, fill=BLACK)
            y += 26
            continue

        for event in group.events:
            if y > max_y - 44:
                draw.text((x, y), "...", font=Fonts.body, fill=BLACK)
                return
            y = _draw_event(draw, event, timezone, x, y, width)
            visible_events += 1

    if visible_events == 0 and all(not group.error for group in groups):
        draw.text((x, y), "Keine Termine", font=Fonts.body, fill=BLACK)


def render_dashboard(
    weather: WeatherData,
    calendar_groups: list[CalendarGroup],
    timezone_name: str,
    resolution: tuple[int, int] = (800, 480),
) -> Image.Image:
    timezone = ZoneInfo(timezone_name)
    now = datetime.now(timezone)
    image = Image.new("RGB", resolution, "white")
    draw = ImageDraw.Draw(image)
    width, height = resolution
    margin = 14
    gap = 24
    header_bottom = 82
    left_width = 318
    right_x = margin + left_width + gap
    right_width = width - right_x - margin

    weekday = WEEKDAYS_DE[now.weekday()]
    date_text = now.strftime("%d.%m.%Y")
    draw.text((margin, 8), weekday, font=Fonts.title, fill=BLACK)
    draw.text((margin, 56), date_text, font=Fonts.subtitle, fill=BLACK)

    footer = f"Stand: {now.strftime('%H:%M')}"
    if weather.error:
        footer += " | Wetter pruefen"
    draw.text((width - _text_width(draw, footer, Fonts.tiny) - margin, 16), footer, font=Fonts.tiny, fill=BLACK)
    draw.line((margin, header_bottom, width - margin, header_bottom), fill=BLACK, width=2)

    content_top = header_bottom + 14
    _draw_calendar_groups(draw, calendar_groups, timezone, margin, content_top, left_width, height - 20)
    _draw_weather_section(image, draw, weather, right_x, content_top, right_width, height - 18)

    return image
