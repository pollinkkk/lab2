class StreamStatsError(Exception):
    """Ошибка, возникающая при некорректной работе с streamstats."""

class UnsupportedFormatError(StreamStatsError):
    """Ошибка неподдерживаемого формата."""

class IncorrectEventError(StreamStatsError):
    """Ошибка неверного события."""

class InvalidTimestampError(StreamStatsError):
    """Ошибка неверной временной метки."""

class ConfigurationCLIError(StreamStatsError):
    """Ошибка конфигурации CLI."""