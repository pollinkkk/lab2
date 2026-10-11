from datetime import datetime
from pathlib import Path

import pytest

from streamstats.analysis import (
    Statistics,
    create_statistics,
    element_processing,
    get_top_5,
)
from streamstats.errors import InvalidTimestampError
from streamstats.models import Event
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import statis_to_dict


def test_unit_invalid_time(tmp_path: Path) -> None:
    """Unit-тест parse_jsonl с некорректным временем."""

    file = tmp_path/ "events.jsonl" 

    file.write_text(
        '{"timestamp":"2026-10-06T22:55:00","level":"INFO","source":"app1","message":"start"}\n'
        '{"timestamp":"2026-10-06T22:57:00","level":"ERROR","source":"app2","message":"error"}\n'
        '{"timestamp":"2026-10-06T22:61:00","level":"INFO","source":"app3","message":"broke"}\n',
        encoding="utf-8"
    )

    with pytest.raises(InvalidTimestampError) as error:
        list(parse_jsonl(str(file), False)) 

   
    assert "строка №3" in str(error.value)
    assert "timestamp" in str(error.value)

def test_unit_parse_csv(tmp_path: Path) -> None:
    """Unit-тест parse_csv."""

    file = tmp_path/ "events.csv" 

    file.write_text(
        "timestamp,level,source,message\n" 
        "2026-10-06T22:39:00,INFO,app1,start\n"
        "2026-10-06T22:40:00,ERROR,app2,error\n"
        "2026-10-06T22:42:00,INVALID,app3,broke\n",
        encoding="utf-8"
    )
    
    rez = list(parse_csv(str(file), True)) # отдельно вызываем функцию парсинга csv файла

    assert len(rez) == 3
    assert rez[0] is not None
    assert rez[1] is not None
    assert rez[2] is None
    assert rez[0].level == "INFO"
    assert rez[0].source == "app1"
    assert rez[1].level == "ERROR"
    assert rez[1].source == "app2"

def test_unit_parse_jsonl(tmp_path: Path) -> None:
    """Unit-тест parse_jsonl."""

    file = tmp_path/ "events.jsonl" 

    file.write_text(
        '{"timestamp":"2026-10-06T22:55:00","level":"INFO","source":"app1","message":"start"}\n'
        '{"timestamp":"2026-10-06T22:57:00","level":"ERROR","source":"app2","message":"error"}\n'
        '{"timestamp":"2026-10-06T22:58:00","level":"INVALID","source":"app3","message":"broke"}\n',
        encoding="utf-8"
    )
    
    rez = list(parse_jsonl(str(file), True))

    assert len(rez) == 3
    assert rez[0] is not None
    assert rez[1] is not None
    assert rez[2] is None
    assert rez[0].level == "INFO"
    assert rez[0].source == "app1"
    assert rez[1].level == "ERROR"
    assert rez[1].source == "app2"

def test_unit_analysis() -> None:
    """Unit-тест analysis."""

    # создаем статистику
    statis = create_statistics()
    timestamp = datetime.fromisoformat('2026-10-10T16:49:00')
    # создаем событие
    event = Event(timestamp, level='INFO', source='app', message='good')
    # запускаем функцию
    element_processing(event, statis)

    assert statis.count_events == 1
    assert statis.levels == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert statis.sources == {
            'app': 1,
        }
    assert statis.error_source == {}
    assert statis.first_timestamp == datetime.fromisoformat('2026-10-10T16:49:00')
    assert statis.last_timestamp == datetime.fromisoformat('2026-10-10T16:49:00')
    assert statis.count_skip == 0

def test_unit_report() -> None:
    """Unit-тест report."""

    # создаем статистику
    statis = Statistics()

    statis.count_events = 3
    statis.levels = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 1,
            'CRITICAL': 0
        } 
    statis.sources = {
            'app': 2,
            'baze': 1
        }

    statis.error_source = {
        'baze': 1
    }
    statis.first_timestamp = datetime.fromisoformat('2026-10-10T16:53:00')
    statis.last_timestamp = datetime.fromisoformat('2026-10-10T16:55:00')
    statis.count_skip = 0

    # создание top_5
    top_5 = [('baze',1)]    
    #вызываем функцию
    stat_dict = statis_to_dict(statis, top_5)

    assert stat_dict['count_events'] == 3
    assert stat_dict['levels'] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 1,
            'CRITICAL': 0
        } 
    assert stat_dict['sources'] ==  {
            'app': 2,
            'baze': 1
        }
    assert stat_dict['top_5_error_sources'] == [('baze',1)]   
    assert stat_dict['first_timestamp'] == '2026-10-10 16:53:00'
    assert stat_dict['last_timestamp'] == '2026-10-10 16:55:00'
    assert stat_dict['count_skip'] == 0

def test_unit_sort_in_top_5() -> None:
    """Unit-тест на проверку сортировки в top_5_errors."""

    # создаем словарь источников с ошибкой
    statis = Statistics()
    statis.error_source = {
        'baze': 1,
        'app': 1,
        'api': 2
    }

    #получаем список кортежей
    rez = get_top_5(statis)

    assert rez == [
        ('api', 2),
        ('app', 1),
        ('baze', 1)
    ]