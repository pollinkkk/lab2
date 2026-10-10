import json
import subprocess
import sys
from pathlib import Path


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
    capture_output=True,
    text=True
    )
    assert res.returncode == 2 
    # проверяем что есть предупреждение с названием
    #  файла и номером строки
    assert "events.csv" in res.stderr
    assert "строка №3" in res.stderr

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
    capture_output=True,
    text=True,
    )
    assert res.returncode == 2 

    assert "events.jsonl" in res.stderr
    assert "строка №2" in res.stderr
    
def test_bad_jsonl_with_skip(tmp_path: Path) -> None:
    """Тест на некорректном файле jsonl с пропуском ошибок."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            '{"timestamp":"2026-10-06T19:32:00","level":"INFO","source":"app1","message":"ok"}\n'
            '{"timestamp":"2026-10-06T19:33:00","level":"DEBUG","source":"api","message":"restart"}\n'
            '{"timestamp":"2026-10-06T19:34:00","level":"INFO","source":"app2","message":"ok"}\n'
            '{"timestamp":"2026-10-06T19:35:00","level":"WARNING","source":"api","message":"stop"}\n'
            '{"timestamp":"2026-10-06T19:36:00","level":"CRITICAL","source":"baze","message":"error"}\n'
            '{"timestamp":"2026-10-06T19:38:00","level":"DEBUG","source":"app1","message":"restart"}\n'
            '{"timestamp":"2026-10-06T19:39:00","level":"ERROR","source":"baze","message":"broke"\n',# сломаный json - нет закрывающей скобки
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
    assert "строка №7" in res.stderr
    
    with open(output_file, encoding="utf-8") as file: 
        rez = json.load(file) 
    
    assert rez["count_events"] == 6
    assert rez["levels"] == {
            'DEBUG': 2,
            'INFO': 2,
            'WARNING': 1,
            'ERROR': 0,
            'CRITICAL': 1
        } 
    assert rez["sources"] == {
            'app1': 2,
            'api': 2,
            'app2': 1,
            'baze': 1,
        }
    assert rez["top_5_error_sources"] == [['baze', 1]]
    assert rez["first_timestamp"] == "2026-10-06 19:32:00"
    assert rez["last_timestamp"] == "2026-10-06 19:38:00"
    assert rez["count_skip"] == 1


def test_empty_csv(tmp_path: Path) -> None:
    """Тест пустого файла."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        "" ,
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

def test_sort_top_5(tmp_path: Path) -> None:
    """Тест на сортировку top_5_sources."""

    input_file = tmp_path/ "events.jsonl" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
        '{"timestamp":"2026-10-06T22:30:00","level":"CRITICAL","source":"приложение","message":"не работает"}\n'
        '{"timestamp":"2026-10-06T22:31:00","level":"ERROR","source":"приложение","message":"приложение упало"}\n'
        '{"timestamp":"2026-10-06T22:32:00","level":"CRITICAL","source":"база","message":"не работает"}\n'
        '{"timestamp":"2026-10-06T22:33:00","level":"ERROR","source":"база","message":"база не отвечает"}\n',
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
  
    assert rez["count_events"] == 4
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 2,
            'CRITICAL': 2
        } 
    assert rez["sources"] == {
            'приложение': 2,
            'база': 2,
        }
    assert rez["top_5_error_sources"] == [['база', 2], ['приложение', 2]]
    assert rez["first_timestamp"] == "2026-10-06 22:30:00"
    assert rez["last_timestamp"] == "2026-10-06 22:33:00"
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

def test_same_statistics(tmp_path: Path) -> None:
    """Тест для проверки статистики из двух файлов csv и jsonl."""

    input_file_1 = tmp_path/ "events_1.csv"
    input_file_2 = tmp_path/ "events_2.jsonl"
    output_file_1 = tmp_path/ "report_1.json"
    output_file_2 = tmp_path/ "report_2.json"

    input_file_1.write_text(
        "timestamp,level,source,message\n"
        "2026-10-09T22:51:00,WARNING,app1,предупреждение\n"
        "2026-10-09T22:52:00,CRITICAL,app2,сломалось\n"
        "2026-10-09T22:53:00,INFO,app3,работает\n",
        encoding="utf-8",
    )

    input_file_2.write_text(
        '{"timestamp":"2026-10-09T22:51:00","level":"WARNING","source":"app1","message":"предупреждение"}\n'
        '{"timestamp":"2026-10-09T22:52:00","level":"CRITICAL","source":"app2","message":"сломалось"}\n'
        '{"timestamp":"2026-10-09T22:53:00","level":"INFO","source":"app3","message":"работает"}\n',
        encoding="utf-8",
    )

    res_1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file_1),
            "--format",
            "csv",
            "--output",
            str(output_file_1)
        ],
        check=False
    )

    res_2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file_2),
            "--format",
            "jsonl",
            "--output",
            str(output_file_2)
        ],
        check=False
    )

    assert res_1.returncode == 0
    assert res_2.returncode == 0

    with open(output_file_1, encoding="utf-8") as file: 
        rez_1 = json.load(file) 

    with open(output_file_2, encoding="utf-8") as file: 
        rez_2 = json.load(file) 

    assert rez_1 == rez_2

def test_immutability_input_file(tmp_path: Path) -> None:
    """Тест на проверку неизменности входного файла."""

    input_file = tmp_path/ "events_.csv"
    output_file = tmp_path/ "report.json"

    text = (
            "timestamp,level,source,message\n"
            "2026-10-09T22:57:00,INFO,app,start\n"
        )
    
    input_file.write_text(
        text,
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
            str(output_file)
        ],
        check=False,
    )
    assert res.returncode == 0
    # проверяем исходный текст и текст в файле после запуска программы
    assert input_file.read_text(encoding="utf-8") == text