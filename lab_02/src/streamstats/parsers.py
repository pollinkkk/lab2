import logging
from collections.abc import Iterator
from csv import DictReader
from datetime import datetime
from json import JSONDecodeError, loads

from .constants import FIELDS, LEVELS
from .errors import IncorrectEventError, InvalidTimestampError, UnsupportedFormatError
from .models import Event

# создание персонального логгера
logger = logging.getLogger(__name__)

def validate_event(dict_line: dict[str, str]) -> Event:
    """Проверка корректности события."""

    # проверка наличия всех полей
    for pole in FIELDS:
        if pole not in dict_line:
            raise UnsupportedFormatError('Не все обязательные поля присутствуют.')

    # сохраняем названия полей
    timestamp = dict_line[FIELDS[0]]
    level = dict_line[FIELDS[1]]
    source = dict_line[FIELDS[2]]
    message = dict_line[FIELDS[3]]

    # проверка допустимости значений полей
    if type(level) != str or level not in LEVELS:
        raise IncorrectEventError('Недопустимое значение level.')

    if type(source) != str or source.strip() == "":
        raise IncorrectEventError('Недопустимое значение source.')

    if type(timestamp) != str:
        raise InvalidTimestampError('Неверная временная метка.')
    
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
        with open(file_name, encoding="utf-8") as file:
            
            file_dicts = DictReader(file)

            # проверяем что поля не пусты, иначе - файл пуст
            if file_dicts.fieldnames is None:
                return
            
            # проход по строкам и их подсчет
            for line_number, line in enumerate(file_dicts, start=2):
               
                try:
                    event = validate_event(line)
                    yield event

                # ловим ошибку при валидации
                # если skip_invalid == True, тогда пропускаем строку и выводим информацию об этом
                # иначе вызываем ошибку и также указываем информацию о ней
                except IncorrectEventError as error:
                    if skip_invalid:
                        logger.warning(
                            f'В файле {file_name} пропущена некорректная строка №{line_number}.')
                        yield None
                    else:
                        raise IncorrectEventError(
                            f'В файле {file_name} строка №{line_number}: {error}') from error

                except InvalidTimestampError as error:
                    if skip_invalid:
                        logger.warning(
                            f'В файле {file_name} пропущена некорректная строка №{line_number}.')
                        yield None
                    else:
                        raise InvalidTimestampError(
                            f'В файле {file_name} строка №{line_number}, поле timestamp: {error}') from error

    # не удалось открыть файл - ошибка
    except FileNotFoundError:
        raise FileNotFoundError("Не удалось открыть файл.")

def parse_jsonl(file_name: str, skip_invalid: bool) -> Iterator[Event | None]:
    """Парсинг файла формата JSONL."""

    try:
        with open(file_name, encoding="utf-8") as file:
            # проход по строкам и их подсчет
            for line_number, line in enumerate(file, start=1):
                try:

                    line_dict = loads(line)

                    # проверяем что преобразованная строка - словарь
                    if type(line_dict) != dict:
                        raise IncorrectEventError(
                            'Событие должно быть объектом.'
    )

                    event = validate_event(line_dict)
                    yield event
                    
                # ловим ошибку, если skip_invalid = True, то пропускаем строку
                # если skip_invalid = False, то вызываем ошибку
                except JSONDecodeError as error:
                    if skip_invalid:
                        logger.warning(
                            f'В файле {file_name} пропущена некорректная строка №{line_number}.')
                        yield None
                    else:
                        raise IncorrectEventError(
                            f'В файле {file_name} строка №{line_number}: Некорректная jsonl-строка.'
                        ) from error

                except IncorrectEventError as error:
                    
                    if skip_invalid:
                        logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                        yield None
                        continue
                    else: 
                        raise IncorrectEventError(
                            f'В файле {file_name} некорректная строка №{line_number}: {error}'
                        ) from error

                except InvalidTimestampError as error:
                                
                    if skip_invalid:
                        logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                        yield None
                    else: 
                        raise InvalidTimestampError(
                            f'В файле {file_name} строка №{line_number}, поле timestamp: {error}'
                        ) from error
                
    except FileNotFoundError:  
        raise FileNotFoundError("Не удалось открыть файл.")

