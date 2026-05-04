from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from calendar_ical import fetch_today_events
from config import load_settings
from display import detect_resolution, save_preview, show_on_inky
from renderer import render_dashboard
from weather import load_weather


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the Inky info dashboard.")
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Only render dashboard_simulation.png and skip the Inky display.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    resolution = (800, 480) if args.no_display else detect_resolution()
    timezone = ZoneInfo(settings.timezone)
    today = datetime.now(timezone).date()

    weather = load_weather(
        city=settings.weather_city,
        api_key=settings.weather_api_key,
        units=settings.weather_units,
        lang=settings.weather_lang,
        timezone_name=settings.timezone,
    )
    calendar_groups = fetch_today_events(settings.calendars, today, settings.timezone)
    image = render_dashboard(weather, calendar_groups, settings.timezone, resolution)

    save_preview(image, settings.preview_path)
    show_on_inky(image, skip_display=args.no_display)


if __name__ == "__main__":
    main()
