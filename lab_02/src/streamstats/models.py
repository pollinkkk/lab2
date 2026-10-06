from datetime import datetime


class Event:
    def __init__(
            self, 
            timestamp: datetime,
            level: str, 
            source: str,
            message: str
    ) -> None:
        """Инициализация класса Event."""

        self.timestamp = timestamp
        self.level = level
        self.source = source
        self.message = message