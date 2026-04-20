from pathlib import Path
import logging


class LoggerService:
    _configured = False

    @classmethod
    def configure(cls, logs_dir: str = "logs", file_name: str = "app.log") -> None:
        if cls._configured:
            return

        log_path = Path(logs_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_path / file_name, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        if not root_logger.handlers:
            root_logger.addHandler(file_handler)

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str, logs_dir: str = "logs") -> logging.Logger:
        cls.configure(logs_dir=logs_dir)
        return logging.getLogger(name)
