import logging
from logging.config import dictConfig
import structlog


def _setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "json": {"()": structlog.stdlib.ProcessorFormatter, "processor": structlog.processors.JSONRenderer()},
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "root": {"level": "INFO", "handlers": ["default"]},
        }
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

_setup_logging()
logger = structlog.get_logger()
