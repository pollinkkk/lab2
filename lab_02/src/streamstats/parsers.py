import logging
from collections.abc import Iterator
from csv import DictReader
from datetime import datetime
from json import JSONDecodeError, loads

from .constants import FIELDS, LEVELS
from .errors import IncorrectEventError, InvalidTimestampError
from .models import Event

# создание персонального логгера
logger = logging.getLogger(__name__)

def validate_event(dict_line: dict[str, str]) -> Event:
    """Проверка корректности события."""

    # проверка наличия всех полей
    for pole in FIELDS:
        if pole not in dict_line:
            raise IncorrectEventError('Не все обязательные поля присутствуют.')

    timestamp = dict_line[FIELDS[0]]
    level = dict_line[FIELDS[1]]
    source = dict_line[FIELDS[2]]
    message = dict_line[FIELDS[3]]

    # проверка допустимости значений полей
    if level not in LEVELS:
        raise IncorrectEventError('Недопустимое значение level.')

    if type(source) != str or source.strip() == "":
        raise IncorrectEventError('Недопустимое значение source.')

    try:
        timestamp_datetime = datetime.fromisoformat(timestamp)
    except ValueError:
        raise InvalidTimestampError('Неверная временная метка.')

    if type(message) != str: 
        raise IncorrectEventError('Недопустимое значение message.')

    event = Event(timestamp_datetime, level, source, message)

    return event

def parse_csv(file_name: str, skip_invalid: bool) -> Iterator[Event | None]:
    """Парсинг файла формата CSV."""

    try:
        with open(f'{file_name}', encoding="utf-8") as file:
            file_dicts = DictReader(file)

            # проход по строкам и их подсчет
            for line_number, line in enumerate(file_dicts, start=2):
                try:
                    event = validate_event(line)
                    yield event
                except (IncorrectEventError, InvalidTimestampError):

                    # ловим ошибку, если skip_invalid = True, то пропускаем строку
                    # если skip_invalid = False, то вызываем ошибку
                    if skip_invalid:
                        logger.warning(f'В файле {file.name} пропущена некорректная строка №{line_number}.')  
                        yield None
                        continue
                    else: 
                        raise
    except FileNotFoundError:  
        raise FileNotFoundError("Не удалось открыть файл.")

def parse_jsonl(file_name: str, skip_invalid: bool) -> Iterator[Event | None]:
    """Парсинг файла формата JSONL."""

    try:
        with open(f'{file_name}', encoding="utf-8") as file:

            # проход по строкам и их подсчет
            for line_number, line in enumerate(file, start=1):
                try:
                    line_dict = loads(line)
                    event = validate_event(line_dict)
                except JSONDecodeError:

                    # ловим ошибку, если skip_invalid = True, то пропускаем строку
                    # если skip_invalid = False, то вызываем ошибку
                    if skip_invalid:
                        logger.warning(f'В файле {file.name} пропущена некорректная строка №{line_number}.')  
                        yield None
                        continue
                    else: 
                        raise IncorrectEventError('Некорректная jsonl-строка')
                except (IncorrectEventError, InvalidTimestampError):

                    # ловим ошибку, если skip_invalid = True, то пропускаем строку
                    # если skip_invalid = False, то вызываем ошибку
                    if skip_invalid:
                        logger.warning(f'В файле {file.name} пропущена некорректная строка №{line_number}.')  
                        yield None
                        continue
                    else: 
                        raise

                yield event
    except FileNotFoundError:  
        raise FileNotFoundError("Не удалось открыть файл.")
