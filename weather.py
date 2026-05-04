from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


CACHE_DIR = Path("/tmp")
CACHE_MAX_AGE_SECONDS = 30 * 60


@dataclass(frozen=True)
class WeatherPoint:
    temperature: float | None
    description: str
    wind: float | None
    icon: str


@dataclass(frozen=True)
class WeatherData:
    now: WeatherPoint
    later: WeatherPoint
    todays_temperatures: list[tuple[datetime, float]]
    error: str | None = None


def _empty_weather(error: str) -> WeatherData:
    fallback = WeatherPoint(
        temperature=None,
        description="Wetter nicht verfuegbar",
        wind=None,
        icon="01d",
    )
    return WeatherData(now=fallback, later=fallback, todays_temperatures=[], error=error)


def _cache_path(city: str) -> Path:
    safe_city = "".join(char if char.isalnum() else "_" for char in city.lower())
    return CACHE_DIR / f"inky_dashboard_forecast_{safe_city}.json"


def _load_cached_forecast(path: Path) -> dict | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_MAX_AGE_SECONDS:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_cached_forecast(path: Path, data: dict) -> None:
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle)
    except OSError:
        pass


def _fetch_forecast(city: str, api_key: str, units: str, lang: str) -> dict:
    cache_path = _cache_path(city)
    cached = _load_cached_forecast(cache_path)
    if cached:
        return cached

    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": api_key, "units": units, "lang": lang},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if "list" not in data:
        raise RuntimeError(data.get("message", "OpenWeatherMap response without forecast list"))
    _save_cached_forecast(cache_path, data)
    return data


def _point_from_item(item: dict) -> WeatherPoint:
    weather = item["weather"][0]
    return WeatherPoint(
        temperature=round(item["main"]["temp"], 1),
        description=str(weather["description"]).capitalize(),
        wind=round(float(item["wind"]["speed"]), 1),
        icon=str(weather["icon"]),
    )


def load_weather(city: str, api_key: str | None, units: str, lang: str, timezone_name: str) -> WeatherData:
    if not api_key:
        return _empty_weather("OpenWeatherMap API key fehlt")

    timezone = ZoneInfo(timezone_name)
    today = datetime.now(timezone).date()

    try:
        data = _fetch_forecast(city, api_key, units, lang)
        forecast_items = data["list"]
        now = _point_from_item(forecast_items[0])
        later = _point_from_item(forecast_items[min(2, len(forecast_items) - 1)])

        todays_temperatures = []
        for item in forecast_items:
            timestamp = datetime.fromtimestamp(item["dt"], tz=timezone)
            if timestamp.date() == today:
                todays_temperatures.append((timestamp, float(item["main"]["temp"])))

        return WeatherData(now=now, later=later, todays_temperatures=todays_temperatures)
    except Exception as exc:
        return _empty_weather(str(exc))

