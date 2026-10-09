import logging
from collections.abc import Iterator
from datetime import datetime

from .constants import FIELDS, LEVELS
from .errors import IncorrectEventError, InvalidTimestampError, UnsupportedFormatError
from .models import Event

# создание персонального логгера
logger = logging.getLogger(__name__)

def read_csv(file_name: str, skip: bool) -> Iterator[dict[str,str] | None]:
    """Чтение csv файла."""
    with open(file_name, encoding="utf-8") as file:
        fields = file.readline().strip().split(',')
        if len(fields)!=4: 
            raise IncorrectEventError("Некорректная csv-строка.")

        while ((line:= file.readline()) != ""):
            values_event = line.strip().split(',', maxsplit=3)
            if len(values_event)!=4: 
                if skip:
                    yield None
                    continue
                else:
                    raise IncorrectEventError("Некорректная csv-строка.")
            event_dict ={
                fields[0]: values_event[0],
                fields[1]: values_event[1],
                fields[2]: values_event[2],
                fields[3]: values_event[3],
            }
            yield event_dict

def read_jsonl(file_name: str, skip: bool) -> Iterator[dict[str, str] | None]:
    """Чтение jsonl файла."""
    with open(file_name, encoding="utf-8") as file:

        while ((line:= file.readline()) != ""):
            clean_line = line.strip()

            if clean_line == "" or clean_line[0] != '{' or clean_line[-1] != '}':
                if skip:
                    yield None
                    continue
                else:
                    raise IncorrectEventError("Некорректная jsonl-строка")

            split_line = clean_line[1:-1].split(',', maxsplit=3) # убираем { и } в начале и конце и сплитуем по ,

            if len(split_line)!=4 : 
                if skip:
                    yield None
                    continue
                else:
                    raise IncorrectEventError("Некорректная jsonl-строка.")

            event_dict = {}

            flag = False
            for row in split_line:
                field = row.split(':',maxsplit=1)

                if len(field) != 2:
                    if skip:
                        flag = True
                        break
                    else:
                        raise IncorrectEventError('Некорретно введено событие.')
                    
                key = field[0].strip().strip('"')
                value = field[1].strip().strip('"')

                event_dict[key] = value

            if flag: 
                yield None
            else:
                yield event_dict

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
        file_dicts = read_csv(file_name, skip_invalid)

        # проход по строкам и их подсчет
        for line_number, line in enumerate(file_dicts, start=2):
            try:
                if line != None:
                    event = validate_event(line)
                    yield event
                else: 
                    logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                    yield None
            except (IncorrectEventError, InvalidTimestampError):

                # ловим ошибку, если skip_invalid = True, то пропускаем строку
                # если skip_invalid = False, то вызываем ошибку
                if skip_invalid:
                    logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                    yield None
                    continue
                else: 
                    raise
    except FileNotFoundError:  
        raise FileNotFoundError("Не удалось открыть файл.")

    except UnsupportedFormatError:
        raise UnsupportedFormatError('Неверные поля файла.')

    except IncorrectEventError:
        raise UnsupportedFormatError('Некорректная csv-строка.')

def parse_jsonl(file_name: str, skip_invalid: bool) -> Iterator[Event | None]:
    """Парсинг файла формата JSONL."""

    try:
        file_dicts = read_jsonl(file_name, skip_invalid)

        # проход по строкам и их подсчет
        for line_number, line in enumerate(file_dicts, start=1):
            try:
                if line != None:
                    event = validate_event(line)
                else: 
                    logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                    yield None
                    continue

            except (IncorrectEventError, InvalidTimestampError):

                # ловим ошибку, если skip_invalid = True, то пропускаем строку
                # если skip_invalid = False, то вызываем ошибку
                if skip_invalid:
                    logger.warning(f'В файле {file_name} пропущена некорректная строка №{line_number}.')  
                    yield None
                    continue
                else: 
                    raise
            yield event
    except FileNotFoundError:  
        raise FileNotFoundError("Не удалось открыть файл.")

    except UnsupportedFormatError:
        raise UnsupportedFormatError('Неверные поля файла.')

    except IncorrectEventError:
        raise UnsupportedFormatError('Некорректная jsonl-строка.')
