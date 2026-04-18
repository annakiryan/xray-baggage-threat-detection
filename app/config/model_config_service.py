import json
from pathlib import Path

from app.domain.entities import (
    ModelConfig,
    ModelInputConfig,
    ModelOutputConfig,
    ModelPostprocessConfig,
)


class ModelConfigService:
    """
    Сервис для загрузки конфигурации ONNX-модели
    """

    REQUIRED_FIELDS = [
        "model_name",
        "model_path",
        "task_type",
        "input",
        "output",
        "postprocess",
        "classes",
    ]

    REQUIRED_INPUT_FIELDS = [
        "width",
        "height",
        "channels",
        "input_name",
        "color_format",
        "normalize",
        "scale",
        "mean",
        "std",
    ]

    REQUIRED_OUTPUT_FIELDS = ["output_names", "format"]

    REQUIRED_POSTPROCESS_FIELDS = ["max_detections"]

    @staticmethod
    def load_model_config(config_path: str | Path) -> ModelConfig:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл конфигурации модели не найден: {path}")

        if path.suffix.lower() != ".json":
            raise ValueError(f"Ожидался JSON-файл конфигурации, получено: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        ModelConfigService._validate_model_config(data, path)

        input_cfg = ModelInputConfig(
            width=int(data["input"]["width"]),
            height=int(data["input"]["height"]),
            channels=int(data["input"]["channels"]),
            input_name=data["input"]["input_name"],
            color_format=data["input"]["color_format"],
            normalize=bool(data["input"]["normalize"]),
            scale=float(data["input"]["scale"]),
            mean=data["input"].get("mean", [0.0, 0.0, 0.0]),
            std=data["input"].get("std", [1.0, 1.0, 1.0]),
        )

        output_cfg = ModelOutputConfig(
            output_names=data["output"]["output_names"],
            format=data["output"]["format"],
        )

        postprocess_cfg = ModelPostprocessConfig(
            confidence_threshold=float(data["postprocess"]["confidence_threshold"]),
            iou_threshold=float(data["postprocess"]["iou_threshold"]),
            max_detections=int(data["postprocess"]["max_detections"]),
        )

        model_config = ModelConfig(
            model_name=data["model_name"],
            task_type=data["task_type"],
            model_path=data["model_path"],
            input=input_cfg,
            output=output_cfg,
            postprocess=postprocess_cfg,
            classes=data["classes"],
        )

        return model_config

    @staticmethod
    def _validate_model_config(data: dict, path: Path) -> None:
        if not isinstance(data, dict):
            raise ValueError(
                f"Некорректная структура JSON в файле {path}: ожидался объект"
            )

        missing_fields = [
            field for field in ModelConfigService.REQUIRED_FIELDS if field not in data
        ]
        if missing_fields:
            raise ValueError(
                f"В конфиге модели отсутствуют обязательные поля: {', '.join(missing_fields)}"
            )

        for field in ModelConfigService.REQUIRED_INPUT_FIELDS:
            if field not in data["input"]:
                raise ValueError(f"В блоке input отсутствует поле '{field}'")

        for field in ModelConfigService.REQUIRED_OUTPUT_FIELDS:
            if field not in data["output"]:
                raise ValueError(f"В блоке output отсутствует поле '{field}'")

        for field in ModelConfigService.REQUIRED_POSTPROCESS_FIELDS:
            if field not in data["postprocess"]:
                raise ValueError(f"В блоке postprocess отсутствует поле '{field}'")

        if not isinstance(data["classes"], list) or not data["classes"]:
            raise ValueError("Поле 'classes' должно быть непустым списком")
