import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class CalendarSource:
    name: str
    url: str


@dataclass(frozen=True)
class Settings:
    weather_api_key: str | None
    weather_city: str
    weather_lang: str
    weather_units: str
    timezone: str
    calendars: list[CalendarSource]
    preview_path: Path


def _load_calendars_from_file(path: Path) -> list[CalendarSource]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        raw_sources = json.load(handle)

    calendars = []
    for item in raw_sources:
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if name and url:
            calendars.append(CalendarSource(name=name, url=url))
    return calendars


def _load_calendars_from_env() -> list[CalendarSource]:
    calendars = []
    for key, value in sorted(os.environ.items()):
        if not key.startswith("CALENDAR_") or key in {"CALENDAR_FILE"}:
            continue
        url = value.strip()
        if not url:
            continue
        name = key.removeprefix("CALENDAR_").replace("_", " ").title()
        calendars.append(CalendarSource(name=name, url=url))
    return calendars


def load_settings() -> Settings:
    load_dotenv(find_dotenv())

    calendar_file = Path(os.getenv("CALENDAR_FILE", BASE_DIR / "calendars.local.json"))
    if not calendar_file.is_absolute():
        calendar_file = BASE_DIR / calendar_file

    calendars = _load_calendars_from_file(calendar_file) or _load_calendars_from_env()

    return Settings(
        weather_api_key=os.getenv("API_KEY") or os.getenv("OPENWEATHER_API_KEY"),
        weather_city=os.getenv("WEATHER_CITY", "Menzingen,CH"),
        weather_lang=os.getenv("WEATHER_LANG", "de"),
        weather_units=os.getenv("WEATHER_UNITS", "metric"),
        timezone=os.getenv("DASHBOARD_TIMEZONE", "Europe/Zurich"),
        calendars=calendars,
        preview_path=BASE_DIR / os.getenv("PREVIEW_PATH", "dashboard_simulation.png"),
    )

