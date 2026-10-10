import csv
import json
import subprocess
import sys
from pathlib import Path


def test_write_to_csv(tmp_path: Path) -> None:
    """Тест с записью результата в csv-файл."""

    input_file = tmp_path/ "events.csv"
    output_file = tmp_path/ "report.csv"

    input_file.write_text(
            "timestamp,level,source,message\n"
            "2026-10-07T10:37:00,INFO,app1,start\n"
            "2026-10-07T10:38:00,ERROR,app2,broke\n",
            encoding="utf-8"
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
            "--format-output",
            "csv",                 # меняем формат файла с результатом
            
        ],
        check=False,
    )
    assert res.returncode == 0

    with open(output_file, encoding="utf-8") as file:
        rez = [row for row in list(csv.reader(file))[1:] if row]

    assert rez[0][1] == "2"
    assert rez[1][1] ==  "{'DEBUG': 0, 'INFO': 1, 'WARNING': 0, 'ERROR': 1, 'CRITICAL': 0}"
    assert rez[2][1] == "{'app1': 1, 'app2': 1}"
    assert rez[3][1] ==  "[('app2', 1)]"
    assert rez[4][1] == "2026-10-07 10:37:00"
    assert rez[5][1] == "2026-10-07 10:38:00"
    assert rez[6][1] == "0"

def test_filter_level(tmp_path: Path) -> None:
    """Тест фильтра по уровню."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            "timestamp,level,source,message\n"
            "2026-10-07T10:57:00,INFO,app1,run\n"
            "2026-10-07T10:58:00,ERROR,baze,broke\n"
            "2026-10-07T10:59:00,WARNING,app1,error\n"
            "2026-10-07T11:00:00,ERROR,api,broke\n"
            "2026-10-07T11:01:00,CRITICAL,baze,stop\n",
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
        "--level",
        "ERROR"
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
            rez = json.load(file) 
        
    assert rez["count_events"] == 2
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 2,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'baze': 1,
            'api': 1,
        }
    assert rez["top_5_error_sources"] == [['api', 1], ['baze', 1]]
    assert rez["first_timestamp"] == "2026-10-07 10:58:00"
    assert rez["last_timestamp"] == "2026-10-07 11:00:00"
    assert rez["count_skip"] == 0

def test_filter_source(tmp_path: Path) -> None:
    """Тест фильтра по источнику."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            "timestamp,level,source,message\n"
            "2026-10-07T10:57:00,INFO,app1,run\n"
            "2026-10-07T10:58:00,ERROR,baze,broke\n"
            "2026-10-07T10:59:00,WARNING,app1,error\n"
            "2026-10-07T11:00:00,ERROR,api,broke\n"
            "2026-10-07T11:01:00,CRITICAL,baze,stop\n",
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
        "--source",
        "app1"
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
            'app1': 2,
        }
    assert rez["top_5_error_sources"] == []
    assert rez["first_timestamp"] == "2026-10-07 10:57:00"
    assert rez["last_timestamp"] == "2026-10-07 10:59:00"
    assert rez["count_skip"] == 0

def test_filter_time(tmp_path: Path) -> None:
    """Тест фильтра по времени."""

    input_file = tmp_path/ "events.csv" 
    output_file = tmp_path / "report.json" 

    input_file.write_text(
            "timestamp,level,source,message\n"
            "2026-10-07T10:57:00,INFO,app1,run\n"
            "2026-10-07T10:58:00,ERROR,baze,broke\n"
            "2026-10-07T10:59:00,WARNING,app1,error\n"
            "2026-10-07T11:00:00,ERROR,api,broke\n"
            "2026-10-07T11:01:00,CRITICAL,baze,stop\n",
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
        "--time",
        "2026-10-07T10:59:00",
        "--flag"
    ],
    check=False, 
    )
    assert res.returncode == 0 
    
    with open(output_file, encoding="utf-8") as file: 
            rez = json.load(file) 
        
    assert rez["count_events"] == 3
    assert rez["levels"] == {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 1,
            'ERROR': 1,
            'CRITICAL': 0
        } 
    assert rez["sources"] == {
            'app1': 2,
            'baze': 1
        }
    assert rez["top_5_error_sources"] == [['baze', 1]]
    assert rez["first_timestamp"] == "2026-10-07 10:57:00"
    assert rez["last_timestamp"] == "2026-10-07 10:59:00"
    assert rez["count_skip"] == 0