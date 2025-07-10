import logging
from logging.config import dictConfig
import structlog

from app.config import settings  


def _setup_logging() -> None:

    log_level = settings.LOG_LEVEL.upper()     

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,           
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "root": {"level": log_level, "handlers": ["default"]},  
        }
    )

    # ─────────────────────────── structlog setup ───────────────────────────
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
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


_setup_logging()

# p
logger = structlog.get_logger()
