from collections.abc import Iterator
from datetime import datetime

from .models import Event


def filter_levels(filter_level: str, events: Iterator[Event]) -> Iterator[Event]:
    """Фильтр по уровням."""

    for event in events:
        if event.level == filter_level:
            yield event

def filter_sources(filter_source: str, events: Iterator[Event]) -> Iterator[Event]:
    """Фильтр по источникам."""

    for event in events:
        if event.source == filter_source:
            yield event

def filter_time(filter_time: datetime, events: Iterator[Event], flag: bool) -> Iterator[Event]:
    """Фильтр по времени."""

    # если flag == True, то пропускаем события до указанного момента,
    # (включительно) иначе - после (включительно)
    if flag:
        for event in events:
            if event.timestamp <= filter_time:
                yield event
    else:
        for event in events:
            if event.timestamp >= filter_time:
                yield event