import json
from pathlib import Path

from app.domain.entities import AppConfig


class ConfigService:
    """
    Сервис для загрузки общего конфига приложения
    """

    REQUIRED_FIELDS = [
        "app_name",
        "logs_dir",
        "models_dir",
        "default_video_dir",
        "default_confidence_threshold",
        "default_iou_threshold",
        "default_frame_skip",
    ]

    @staticmethod
    def load_app_config(config_path: str | Path) -> AppConfig:
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {path}")

        if path.suffix.lower() != ".json":
            raise ValueError(f"Ожидался JSON-файл конфигурации, получено: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        ConfigService._validate_app_config(data, path)

        return AppConfig(
            app_name=data["app_name"],
            logs_dir=data["logs_dir"],
            models_dir=data["models_dir"],
            default_video_dir=data["default_video_dir"],
            default_confidence_threshold=float(data["default_confidence_threshold"]),
            default_iou_threshold=float(data["default_iou_threshold"]),
            default_frame_skip=int(data["default_frame_skip"]),
            device=data["device"],
        )

    @staticmethod
    def _validate_app_config(data: dict, path: Path) -> None:
        if not isinstance(data, dict):
            raise ValueError(
                f"Некорректная структура JSON в файле {path}: ожидался объект"
            )

        missing_fields = [
            field_name
            for field_name in ConfigService.REQUIRED_FIELDS
            if field_name not in data
        ]

        if missing_fields:
            missing_str = ", ".join(missing_fields)
            raise ValueError(
                f"В конфиге приложения отсутствуют обязательные поля: {missing_str}"
            )

        if not isinstance(data["app_name"], str) or not data["app_name"].strip():
            raise ValueError("Поле 'app_name' должно быть непустой строкой")

        if not isinstance(data["logs_dir"], str) or not data["logs_dir"].strip():
            raise ValueError("Поле 'logs_dir' должно быть непустой строкой")

        if not isinstance(data["models_dir"], str) or not data["models_dir"].strip():
            raise ValueError("Поле 'models_dir' должно быть непустой строкой")

        if (
            not isinstance(data["default_video_dir"], str)
            or not data["default_video_dir"].strip()
        ):
            raise ValueError("Поле 'default_video_dir' должно быть непустой строкой")

        if (
            float(data["default_confidence_threshold"]) < 0
            or float(data["default_confidence_threshold"]) > 1
        ):
            raise ValueError(
                "Поле 'default_confidence_threshold' должно быть в диапазоне [0, 1]"
            )

        if (
            float(data["default_iou_threshold"]) < 0
            or float(data["default_iou_threshold"]) > 1
        ):
            raise ValueError(
                "Поле 'default_iou_threshold' должно быть в диапазоне [0, 1]"
            )

        if int(data["default_frame_skip"]) < 1:
            raise ValueError("Поле 'default_frame_skip' должно быть >= 1")
