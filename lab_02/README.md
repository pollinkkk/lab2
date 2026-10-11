# Лабораторная работа №2. Потоковый анализатор файлов

## Описание

Программа `streamstats` предназначена для чтения событий из файлов формата CSV и JSONL и формирования статистики по этим событиям.

Программа умеет:
- читать CSV и JSONL файлы;
- обрабатывать несколько файлов;
- проверять корректность событий;
- считать количество событий;
- считать количество событий каждого уровня;
- считать количество событий каждого источника;
- находить top-5 источников ошибок уровней `ERROR` и `CRITICAL`;
- находить первую и последнюю временную метку;
- пропускать некорректные строки с помощью `--skip-invalid`;
- сохранять результат в JSON или CSV;
- фильтровать события по уровню, источнику и времени.

## Структура проекта

```text
lab_02/
├── src/
│   └── streamstats/
│       ├── __init__.py
│       ├── __main__.py
│       ├── analysis.py
│       ├── constants.py
│       ├── errors.py
│       ├── filters.py
│       ├── models.py
│       ├── parsers.py
│       └── report.py
├── tests/
│   ├── test_cli.py
|   ├── test_unit.py
|   └── test_additional.py
├── pyproject.toml
└── README.md
```

### Основные файлы

- `__main__.py` — точка входа в программу и обработка аргументов командной строки.
- `models.py` — класс `Event`.
- `parsers.py` — чтение и проверка CSV и JSONL файлов.
- `analysis.py` — сбор статистики по событиям.
- `filters.py` — фильтры по уровню, источнику и времени.
- `report.py` — запись результата в JSON и CSV.
- `errors.py` — пользовательские исключения.
- `constants.py` — константы программы.
- `test_cli.py` — интеграционные тесты командной строки.
- `test_unit.py` — модульные тесты отдельных функций.
- `test_additional.py` — тесты дополнительных возможностей программы.

## Запуск программы

Перед запуском необходимо создать и активировать виртуальное окружение.

Для Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Установить проект:

```powershell
pip install -e .
```

Установить инструменты для тестирования и проверки кода:

```powershell
pip install pytest ruff mypy
```

Основной формат запуска:

```powershell
python -m streamstats analyze INPUT --format csv --output report.json
```

Для JSONL:

```powershell
python -m streamstats analyze events.jsonl --format jsonl --output report.json
```

Можно передать несколько файлов:

```powershell
python -m streamstats analyze events1.csv events2.csv --format csv --output report.json
```

## Аргументы

- `INPUT` — один или несколько входных файлов.
- `--format` — формат входного файла: `csv` или `jsonl`.
- `--output` — файл для записи результата.
- `--skip-invalid` — пропускать некорректные строки.
- `--format-output` — формат отчёта: `json` или `csv`.
- `--level` — фильтр по уровню события.
- `--source` — фильтр по источнику события.
- `--time` — фильтр по времени.
- `--flag` — если указан, выбираются события до заданного времени включительно; без него — после заданного времени включительно.

### Обработка некорректных данных
- Без `--skip-invalid` программа прекращает обработку при обнаружении некорректного события, выводит сообщение об ошибке с названием файла и номером строки и завершается с кодом 2.
- С `--skip-invalid` некорректная строка пропускается, в лог записывается предупреждение, а количество пропущенных строк учитывается в отчёте.

Получить справку:

```powershell
python -m streamstats --help
```

## Примеры

Пропуск некорректных строк:

```powershell
python -m streamstats analyze events.csv --format csv --output report.json --skip-invalid
```

Фильтр по уровню:

```powershell
python -m streamstats analyze events.csv --format csv --output report.json --level ERROR
```

Фильтр по источнику:

```powershell
python -m streamstats analyze events.csv --format csv --output report.json --source app
```

Фильтр по времени:

```powershell
python -m streamstats analyze events.csv --format csv --output report.json --time 2026-10-07T10:00:00
```

С флагом `--flag`:

```powershell
python -m streamstats analyze events.csv --format csv --output report.json --time 2026-10-07T10:00:00 --flag
```

Запись отчёта в CSV:

```powershell
python -m streamstats analyze events.csv --format csv --output report.csv --format-output csv
```

## Тестирование

Для проверки программы используются тесты `pytest`.

Запуск тестов:

```powershell
python -m pytest
```

В тестах проверяются:
- корректные CSV и JSONL файлы;
- некорректные строки;
- работа `--skip-invalid`;
- пустой файл;
- Unicode;
- обработка нескольких файлов;
- работа CLI;
- фильтры;
- запись результата в CSV;
- запуск `--help`.

Проверка стиля кода:

```powershell
ruff check .
```

Проверка типов:

```powershell
python -m mypy .
```