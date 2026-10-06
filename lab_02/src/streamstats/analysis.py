from collections.abc import Iterator
from datetime import datetime

from .models import Event


class Statistics:
    """Класс для отображения статистики."""
    
    def __init__(self) -> None:
        self.count_events = 0
        self.levels = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        }
        self.sources: dict[str, int] = {}
        self.error_source: dict[str, int] = {}
        self.first_timestamp: datetime | None = None
        self.last_timestamp: datetime | None = None
        self.count_skip = 0

def create_statistics() -> Statistics:
    """Создание пустой статистики."""

    return Statistics()

def cleaning_iterator(events: Iterator[Event | None], statis: Statistics) -> Iterator[Event]:
    """Очистка потока от None."""

    for element in events:
        if element == None:
            statis.count_skip += 1
        else:
            yield element

def element_processing(
        element: Event , 
        statis: Statistics
    ) -> None:
    """Обработка одного элемента."""

    # обновление счетчика count_events
    statis.count_events += 1

    # обновление счетчика level
    levels = statis.levels
    current_level = element.level
    levels[current_level] += 1

    # обновление счетчика sourse
    sources = statis.sources
    current_source = element.source
    if current_source in sources: 
        sources[current_source] += 1
    else:
        sources[current_source] = 1

    # обновление счетчика error_source
    if current_level in ('ERROR', 'CRITICAL'):
        error_sources = statis.error_source
        if current_source in error_sources:
            error_sources[current_source] += 1
        else:
            error_sources[current_source] = 1

    # обновление временных меток
    current_timestamp = element.timestamp
    if statis.first_timestamp == None:
        statis.first_timestamp = current_timestamp

    if statis.last_timestamp == None:
        statis.last_timestamp = current_timestamp

    statis.first_timestamp = min(statis.first_timestamp, current_timestamp)

    statis.last_timestamp = max(statis.last_timestamp, current_timestamp)

def get_top_5(
        statis: Statistics
    ) -> list[tuple[str, int]]:
    """Получение top-5 источников ошибок уровня ERROR/CRITICAL."""

    error_sources = statis.error_source
    sort_error_sources = sorted(error_sources.items(), key=lambda x: x[1], reverse=True)
    top_5 = sort_error_sources[:5]

    return top_5