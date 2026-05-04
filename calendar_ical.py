from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import recurring_ical_events
import requests
from icalendar import Calendar

from config import CalendarSource


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: datetime | date
    end: datetime | date | None
    all_day: bool


@dataclass(frozen=True)
class CalendarGroup:
    name: str
    events: list[CalendarEvent]
    error: str | None = None


def _as_local_datetime(value: datetime | date, timezone: ZoneInfo) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone)
        return value.astimezone(timezone)
    return datetime.combine(value, time.min, tzinfo=timezone)


def _is_all_day(value: datetime | date) -> bool:
    return not isinstance(value, datetime)


def _event_from_component(component, timezone: ZoneInfo) -> CalendarEvent:
    start = component.decoded("DTSTART")
    end = component.decoded("DTEND") if component.get("DTEND") else None
    title = str(component.get("SUMMARY", "Ohne Titel")).strip() or "Ohne Titel"
    return CalendarEvent(
        title=title,
        start=start,
        end=end,
        all_day=_is_all_day(start),
    )


def _fetch_calendar(url: str) -> Calendar:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return Calendar.from_ical(response.content)


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, requests.RequestException):
        return "Kalender nicht erreichbar"
    return "Kalender konnte nicht gelesen werden"


def fetch_today_events(
    sources: list[CalendarSource],
    target_date: date,
    timezone_name: str,
) -> list[CalendarGroup]:
    timezone = ZoneInfo(timezone_name)
    day_start = datetime.combine(target_date, time.min, tzinfo=timezone)
    day_end = datetime.combine(target_date, time.max, tzinfo=timezone)

    groups = []
    for source in sources:
        try:
            calendar = _fetch_calendar(source.url)
            components = recurring_ical_events.of(calendar).between(day_start, day_end)
            events = [_event_from_component(component, timezone) for component in components]
            events.sort(
                key=lambda event: (
                    0 if event.all_day else 1,
                    _as_local_datetime(event.start, timezone),
                    event.title.lower(),
                )
            )
            groups.append(CalendarGroup(name=source.name, events=events))
        except Exception as exc:
            groups.append(CalendarGroup(name=source.name, events=[], error=_friendly_error(exc)))

    return groups
