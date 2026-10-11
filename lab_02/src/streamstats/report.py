import json
from csv import writer

from .analysis import Statistics


def statis_to_dict(statis: Statistics, top_5: list[tuple[str, int]]) -> dict[str, int | str | dict | list[tuple[str, int]] | None]:
    """Конвертация объекта класса Statistics в словарь."""

    statis_dict: dict[str, int | str | dict | list[tuple[str, int]] | None] = {
        'count_events': statis.count_events,
        'levels': statis.levels,
        'sources': statis.sources,
        'top_5_error_sources': top_5,
        'first_timestamp': str(statis.first_timestamp) if statis.first_timestamp is not None else None,
        'last_timestamp': str(statis.last_timestamp) if statis.last_timestamp is not None else None,
        'count_skip': statis.count_skip
    }

    return statis_dict

def write_to_json_file(statis: dict[str, int | str | dict | list[tuple[str, int]] | None] , output_file: str) -> None:
    """Запись статистики в json файл."""
    
    with open(output_file, "w", encoding="utf-8", newline="") as file:
        json.dump(statis, file, ensure_ascii=False, indent=4)

def write_to_csv_file(statis: dict[str, int | str | dict | list[tuple[str, int]] | None] , output_file: str) -> None:
    """Запись статистики в csv файл (доп)."""
    
    with open(output_file, "w", encoding="utf-8", newline="") as file:
        csv_writer = writer(file)

        # записать строку с заголовками
        csv_writer.writerow(["metric", "value"])

        # записать основные данные
        for key, value in statis.items():
            csv_writer.writerow([key, value])