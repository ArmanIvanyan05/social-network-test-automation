"""Structured JSON logging configuration."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

RESERVED_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    """Render standard logs as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record and its structured extras."""
        event: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in RESERVED_LOG_RECORD_FIELDS and key not in event
            }
        )
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, default=str, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure process-wide structured console logging once."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
