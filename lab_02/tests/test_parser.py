import json
import subprocess
import sys
from pathlib import Path

import pytest

from streamstats.errors import InvalidTimestampError
from streamstats.parsers import parse_csv, parse_jsonl


def test_good_csv(tmp_path: Path) -> None:
    """Тест на корректном файле csv."""

    input_file = tmp_path/ "events.csv" # путь для файла со входными данными
    output_file = tmp_path / "report.json" # путь для файла для записи результата

    input_file.write_text(
        "timestamp,level,source,message\n" # записываем входные данные
        "2026-10-06T18:54:00,INFO,app1,start\n"
        "2026-10-06T18:55:00,ERROR,app2,broke\n",
        encoding="utf-8"
    )

    res = subprocess.run(  # запускаем программу
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "csv",
        "--output",
        str(output_file),
    ],
    check=False, # не нужно автоматичсеки проверять код завершения программы
    )
    assert res.returncode == 0 # проверяем, что прогамма запустилась успешно
    
    with open(output_file, encoding="utf-8") as file: # открыли файл для чтения результата
        rez = json.load(file) # превращает json файл в словарь: нужно для сверки результата
    
    # сверяем каждое значение статистики
    assert rez["count_events"] == 2
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 0,
            'ERROR': 1,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'app1': 1,
            'app2': 1,
        }
    assert rez["top_5_error_sources"] == [['app2', 1]]
    assert rez["first_timestamp"] == "2026-10-06 18:54:00"
    assert rez["last_timestamp"] == "2026-10-06 18:55:00"
    assert rez["count_skip"] == 0

def test_good_jsonl(tmp_path: Path) -> None:
    """Тест на корректном файле jsonl."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        '{"timestamp":"2026-10-06T19:01:00","level":"INFO","source":"app","message":"hello"}\n'
        '{"timestamp":"2026-10-06T19:02:00","level":"WARNING","source":"server","message":"good bay"}\n',
        encoding="utf-8",
    )

    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "jsonl",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
  
    assert rez["count_events"] == 2
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'app': 1,
            'server': 1,
        }
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == "2026-10-06 19:01:00"
    assert rez["last_timestamp"] == "2026-10-06 19:02:00"
    assert rez["count_skip"] == 0

def test_bad_csv_not_skip(tmp_path: Path) -> None:
    """Тест на некорректном файле csv без пропуска ошибок."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-06T19:05:00,INFO,app,all good\n"
        "2026-10-06T19:06:00,ERROR\n", # поврежденная строка
        encoding="utf-8",
    )
    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "csv",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 2 

def test_bad_csv_with_skip(tmp_path: Path) -> None:
    """Тест на некорректном файле csv с пропуском ошибок."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            "timestamp,level,source,message\n"
            "2026-10-06T19:24:00,INFO,app,all good\n"
            "2026-10-06T19:26:00,ERROR\n", # поврежденная строка
            encoding="utf-8",
        )
    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "csv",
        "--output",
        str(output_file),
        "--skip-invalid",
        
    ],
    check=False, 
    capture_output=True, # сохраняем вывод программы
    text=True, # преобразуем вывод в текст
    )
    assert res.returncode == 0 
    assert "events.csv" in res.stderr # проверяем что выводится файл, в котором пропущена строка
    assert "строка №3" in res.stderr # проверяем что выводится номер пропущенной строки
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 1
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'app': 1,
        }
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == "2026-10-06 19:24:00"
    assert rez["last_timestamp"] == "2026-10-06 19:24:00"
    assert rez["count_skip"] == 1

def test_invalid_level(tmp_path: Path) -> None:
    """Тест на некорректном файле csv(недопустимый уровень) без пропуска ошибок."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-06T19:18:00,INFO,app,all good\n"
        "2026-10-06T19:20:00,HELP,db,error\n", # несуществующий level
        encoding="utf-8",
    )
    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "csv",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 2 
    
def test_unit_invalid_time(tmp_path: Path) -> None:
    """Unit-тест parse_jsonl с некорректным временем."""

    file = tmp_path/ "events.jsonl" 

    file.write_text(
        '{"timestamp":"2026-10-06T22:55:00","level":"INFO","source":"app1","message":"start"}\n'
        '{"timestamp":"2026-10-06T22:57:00","level":"ERROR","source":"app2","message":"error"}\n'
        '{"timestamp":"2026-10-06T22:61:00","level":"INFO","source":"app3","message":"broke"}\n',
        encoding="utf-8"
    )

    with pytest.raises(InvalidTimestampError):
        list(parse_jsonl(str(file), False))

   

def test_bad_jsonl_not_skip(tmp_path: Path) -> None:
    """Тест на некорректном файле jsonl без пропуска ошибок."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        '{"timestamp":"2026-10-06T19:29:00","level":"INFO","source":"app","message":"ok"}\n'
        '{"timestamp":"2026-10-06T19:31:00","level":"ERROR","source":"db","message":"ops"\n',# сломаный json - нет закрывающей скобки
        encoding="utf-8",
    )
    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "jsonl",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 2 
    
def test_bad_jsonl_with_skip(tmp_path: Path) -> None:
    """Тест на некорректном файле jsonl с пропуском ошибок."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            '{"timestamp":"2026-10-06T19:32:00","level":"INFO","source":"app","message":"ok"}\n'
            '{"timestamp":"2026-10-06T19:33:00","level":"ERROR","source":"baze","message":"ops"\n',# сломаный json - нет закрывающей скобки
            encoding="utf-8",
        )

    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "jsonl",
        "--output",
        str(output_file),
        "--skip-invalid",
        
    ],
    check=False, 
    capture_output=True,
    text=True,
    )
    assert res.returncode == 0 
    assert "events.jsonl" in res.stderr
    assert "строка №2" in res.stderr
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 1
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'app': 1,
        }
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == "2026-10-06 19:32:00"
    assert rez["last_timestamp"] == "2026-10-06 19:32:00"
    assert rez["count_skip"] == 1


def test_empty_csv(tmp_path: Path) -> None:
    """Тест пустого файла."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        "timestamp,level,source,message\n" ,
        encoding="utf-8"
    )

    res = subprocess.run(  # запускаем программу
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "csv",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 0
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {}
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == None
    assert rez["last_timestamp"] == None
    assert rez["count_skip"] == 0

def test_empty_jsonl(tmp_path: Path) -> None:
    """Тест пустого файла."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        ""
    )

    res = subprocess.run(  # запускаем программу
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "jsonl",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 0
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {}
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == None
    assert rez["last_timestamp"] == None
    assert rez["count_skip"] == 0

def test_unicode(tmp_path: Path) -> None:
    """Тест на Unicode в файле jsonl."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        '{"timestamp":"2026-10-06T22:30:00","level":"INFO","source":"приложение","message":"работает"}\n'
        '{"timestamp":"2026-10-06T22:31:00","level":"ERROR","source":"база","message":"упало"}\n',
        encoding="utf-8",
    )

    res = subprocess.run( 
    [
        sys.executable,
        "-m",
        "streamstats",
        "analyze",
        str(input_file),
        "--format",
        "jsonl",
        "--output",
        str(output_file),
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
  
    assert rez["count_events"] == 2
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 0,
            'ERROR': 1,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'приложение': 1,
            'база': 1,
        }
    assert rez["top_5_error_sources"] == [['база', 1]]
    assert rez["first_timestamp"] == "2026-10-06 22:30:00"
    assert rez["last_timestamp"] == "2026-10-06 22:31:00"
    assert rez["count_skip"] == 0

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
    assert rez[0] != None
    assert rez[1] != None
    assert rez[2] == None
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
    assert rez[0] != None
    assert rez[1] != None
    assert rez[2] == None
    assert rez[0].level == "INFO"
    assert rez[0].source == "app1"
    assert rez[1].level == "ERROR"
    assert rez[1].source == "app2"


def test_two_files(tmp_path: Path) -> None:
    """Тест ввода нескольких файлов."""

    input_file_1 = tmp_path/ "events_1.csv" 
    input_file_2 = tmp_path/ "events_2.csv" 
    output_file = tmp_path/ "report.json"

    input_file_1.write_text(
        "timestamp,level,source,message\n"
        "2026-10-06T23:06:00,INFO,app1,запустилось\n"
        "2026-10-06T23:07:00,ERROR,app2,сломалось\n",
        encoding="utf-8",
    )

    input_file_2.write_text(
        "timestamp,level,source,message\n"
        "2026-10-06T23:13:00,WARNING,app1,предупреждение\n"
        "2026-10-06T23:15:00,CRITICAL,app2,сломалось\n",
        encoding="utf-8",
        )
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file_1),
            str(input_file_2),
            "--format",
            "csv",
            "--output",
            str(output_file),
        ],
        check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 4
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 1,
            'CRITICAL': 1
        } 
    assert rez["sources"] == {
            'app1': 2,
            'app2': 2,
        }
    assert rez["top_5_error_sources"] == [['app2', 2]]
    assert rez["first_timestamp"] == "2026-10-06 23:06:00"
    assert rez["last_timestamp"] == "2026-10-06 23:15:00"
    assert rez["count_skip"] == 0

def test_help() -> None:
    """Тест команды --help."""

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "--help"
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "usage:" in res.stdout
    assert "{analyze}" in res.stdout
    assert "--format {csv,jsonl}" in res.stdout
    assert "--output OUTPUT" in res.stdout
    assert "--skip-invalid" in res.stdout

