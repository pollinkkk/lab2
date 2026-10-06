import argparse
import sys
from datetime import datetime

from .analysis import (
    cleaning_iterator,
    create_statistics,
    element_processing,
    get_top_5,
)
from .errors import InvalidTimestampError, StreamStatsError
from .filters import filter_levels, filter_sources, filter_time
from .parsers import parse_csv, parse_jsonl
from .report import statis_to_dict, write_to_csv_file, write_to_json_file


def main() -> None:
    """Точка входа в программу."""

    try:
        parser = argparse.ArgumentParser()

        parser.add_argument("command", choices=["analyze"])
        parser.add_argument("INPUT", nargs='+')
        parser.add_argument("--format", choices=["csv", "jsonl"], required=True)
        parser.add_argument(
            "--format-output", 
            choices=["csv", "json"], 
            default="json"
            )
        parser.add_argument("--output", required=True)
        parser.add_argument("--skip-invalid", action="store_true")
        # аргументы для фильтров
        parser.add_argument("--level", default=None)
        parser.add_argument("--source", default=None)
        parser.add_argument("--time", default=None)
        parser.add_argument("--flag", action="store_true")

        args = parser.parse_args()

        if args.command == "analyze":
            statis = create_statistics()

            # перебираем файлы с ввода
            for file in args.INPUT:
                if args.format == 'csv':
                    events = parse_csv(file, args.skip_invalid)
                else:
                    events = parse_jsonl(file, args.skip_invalid)

                # очищаем поток от None
                clean_events = cleaning_iterator(events, statis)

                # проверяем фильтры
                if args.level != None:
                    clean_events = filter_levels(args.level, clean_events)

                if args.source != None:
                    clean_events = filter_sources(args.source, clean_events)

                if args.time != None:
                    try:
                        iso_datetime = datetime.fromisoformat(args.time)
                    except ValueError as error:
                        raise InvalidTimestampError(
                            "Неверный формат времени."
                            ) from error
                    
                    clean_events = filter_time(
                        iso_datetime, 
                        clean_events, 
                        args.flag
                        )

                # проходимся по полученному итератору событий
                for element in clean_events:
                    element_processing(element, statis)

        # берем топ-5 источников с ошибками для статистики
        top_5 = get_top_5(statis)

        # превращаем статистику из класса Statistic в словарь
        dict_statis = statis_to_dict(statis, top_5)

        # записываем в файл нужного формата
        if args.format_output == 'csv':
            write_to_csv_file(dict_statis, args.output)

        if args.format_output == 'json':
            write_to_json_file(dict_statis, args.output)

    except StreamStatsError as error:
        print(error, file=sys.stderr)
        sys.exit(2)

    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()