import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from app.config.setting import settings
from app.utils.path import find_project_root

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """Console formatter that colorizes the level name (ANSI)."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelname)
        if color:
            return f"{color}{msg}{self.RESET}"
        return msg


def _level_from_env() -> int:
    return _LEVELS.get(settings.app.log_level, logging.INFO)


def setup_logging() -> None:
    """Configure root logging: colored console + daily-rotated files.

    Idempotent — safe to call more than once (e.g. from generator + app).
    """
    root = logging.getLogger()
    if root.handlers:
        return

    level = _level_from_env()
    root.setLevel(level)

    log_dir = find_project_root() / "logs"
    log_dir.mkdir(exist_ok=True)

    plain = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    colored = ColoredFormatter(_LOG_FORMAT, datefmt=_DATE_FORMAT, use_color=True)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(colored)
    root.addHandler(console)

    info_file = TimedRotatingFileHandler(
        log_dir / "app.log", when="midnight", interval=1,
        backupCount=30, encoding="utf-8",
    )
    info_file.suffix = "%Y-%m-%d"
    info_file.setFormatter(plain)
    root.addHandler(info_file)

    error_file = TimedRotatingFileHandler(
        log_dir / "app.error.log", when="midnight", interval=1,
        backupCount=30, encoding="utf-8",
    )
    error_file.suffix = "%Y-%m-%d"
    error_file.setFormatter(plain)
    error_file.setLevel(logging.ERROR)
    root.addHandler(error_file)

    logging.info("Logging initialised (level=%s)", logging.getLevelName(level))
