import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """
    Базовая настройка логирования для всего приложения.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=handlers,
    )

    # Убавим болтовню некоторых библиотек, если нужно
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("arango").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
