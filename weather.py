from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
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
    temperature_title: str = "Temperatur heute"
    error: str | None = None


def _empty_weather(error: str) -> WeatherData:
    fallback = WeatherPoint(
        temperature=None,
        description="Wetter nicht verfügbar",
        wind=None,
        icon="01d",
    )
    return WeatherData(now=fallback, later=fallback, todays_temperatures=[], error=error)


def _cache_path(city: str, cache_date: str, kind: str) -> Path:
    safe_city = "".join(char if char.isalnum() else "_" for char in city.lower())
    return CACHE_DIR / f"inky_dashboard_{kind}_{safe_city}_{cache_date}.json"


def _load_cached_forecast(path: Path, allow_stale: bool = False) -> dict | None:
    if not path.exists():
        return None
    if not allow_stale and time.time() - path.stat().st_mtime > CACHE_MAX_AGE_SECONDS:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_cached_forecast(path: Path, data: dict) -> None:
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle)
    except OSError:
        pass


def _load_graph_temperatures(path: Path, timezone: ZoneInfo) -> list[tuple[datetime, float]] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        raw_points = json.load(handle)
    return [
        (datetime.fromisoformat(timestamp).astimezone(timezone), float(temperature))
        for timestamp, temperature in raw_points
    ]


def _save_graph_temperatures(path: Path, points: list[tuple[datetime, float]]) -> None:
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(
                [(timestamp.isoformat(), temperature) for timestamp, temperature in points],
                handle,
            )
    except OSError:
        pass


def _fetch_forecast(city: str, api_key: str, units: str, lang: str, cache_date: str) -> dict:
    cache_path = _cache_path(city, cache_date, "forecast")
    cached = _load_cached_forecast(cache_path)
    if cached:
        return cached

    try:
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
    except Exception:
        stale = _load_cached_forecast(cache_path, allow_stale=True)
        if stale:
            return stale
        raise


def _fetch_current_weather(city: str, api_key: str, units: str, lang: str, cache_date: str) -> dict:
    cache_path = _cache_path(city, cache_date, "current")
    cached = _load_cached_forecast(cache_path)
    if cached:
        return cached

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": units, "lang": lang},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if "main" not in data or "weather" not in data:
            raise RuntimeError(data.get("message", "OpenWeatherMap response without current weather"))
        _save_cached_forecast(cache_path, data)
        return data
    except Exception:
        stale = _load_cached_forecast(cache_path, allow_stale=True)
        if stale:
            return stale
        raise


def _point_from_item(item: dict) -> WeatherPoint:
    weather = item["weather"][0]
    return WeatherPoint(
        temperature=round(item["main"]["temp"], 1),
        description=str(weather["description"]).capitalize(),
        wind=round(float(item["wind"]["speed"]), 1),
        icon=str(weather["icon"]),
    )


def _timestamp_from_item(item: dict, timezone: ZoneInfo) -> datetime:
    return datetime.fromtimestamp(item["dt"], tz=timezone)


def _closest_forecast_item(items: list[dict], target: datetime) -> dict:
    return min(items, key=lambda item: abs((_timestamp_from_item(item, target.tzinfo) - target).total_seconds()))


def _build_graph_temperatures(
    forecast_items: list[dict],
    timezone: ZoneInfo,
    today,
    current_data: dict | None,
    current_time: datetime,
) -> list[tuple[datetime, float]]:
    graph_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone) + timedelta(hours=3)
    graph_end = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone)
    graph_temperatures = []

    for item in forecast_items:
        timestamp = _timestamp_from_item(item, timezone)
        if graph_start <= timestamp <= graph_end:
            graph_temperatures.append((timestamp, float(item["main"]["temp"])))

    graph_temperatures.sort(key=lambda point: point[0])

    if (
        len(graph_temperatures) == 1
        and current_data
        and graph_start <= current_time <= graph_end
        and current_time < graph_temperatures[0][0]
    ):
        graph_temperatures.insert(0, (current_time, float(current_data["main"]["temp"])))

    return graph_temperatures


def load_weather(city: str, api_key: str | None, units: str, lang: str, timezone_name: str) -> WeatherData:
    if not api_key:
        return _empty_weather("OpenWeatherMap API-Key fehlt")

    timezone = ZoneInfo(timezone_name)
    today = datetime.now(timezone).date()

    try:
        forecast_date = today.strftime("%Y%m%d")
        data = _fetch_forecast(city, api_key, units, lang, forecast_date)
        forecast_items = data["list"]
        try:
            current_data = _fetch_current_weather(city, api_key, units, lang, today.strftime("%Y%m%d"))
            current_time = _timestamp_from_item(current_data, timezone)
            now = _point_from_item(current_data)
        except Exception:
            current_data = None
            current_time = datetime.now(timezone)
            now = _point_from_item(forecast_items[0])

        later_target = current_time + timedelta(hours=6)
        later = _point_from_item(_closest_forecast_item(forecast_items, later_target))

        graph_cache_path = _cache_path(city, forecast_date, "graph")
        graph_temperatures = _load_graph_temperatures(graph_cache_path, timezone)
        if graph_temperatures is None:
            graph_temperatures = _build_graph_temperatures(
                forecast_items=forecast_items,
                timezone=timezone,
                today=today,
                current_data=current_data,
                current_time=current_time,
            )
            _save_graph_temperatures(graph_cache_path, graph_temperatures)

        if len(graph_temperatures) >= 2:
            return WeatherData(now=now, later=later, todays_temperatures=graph_temperatures)

        return WeatherData(
            now=now,
            later=later,
            todays_temperatures=[],
            temperature_title="Temperatur heute",
        )
    except Exception as exc:
        return _empty_weather(str(exc))
