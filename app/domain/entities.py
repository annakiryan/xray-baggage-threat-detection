from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any


@dataclass
class Detection:
    """
    Одна детекция на кадре
    """

    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)


@dataclass
class FrameResult:
    """
    Результат обработки одного кадра
    """

    frame: Any
    detections: List[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    fps: float = 0.0


@dataclass
class AppConfig:
    """
    Общий конфиг приложения
    """

    app_name: str
    logs_dir: str
    models_dir: str
    default_video_dir: str
    default_confidence_threshold: float
    default_iou_threshold: float
    default_frame_skip: int


@dataclass
class ModelInputConfig:
    """
    Параметры входа модели
    """

    width: int
    height: int
    channels: int
    input_name: str
    color_format: str
    normalize: bool
    scale: float


@dataclass
class ModelOutputConfig:
    """
    Параметры выхода модели
    """

    output_names: List[str]
    format: str


@dataclass
class ModelPostprocessConfig:
    """
    Параметры постобработки
    """

    max_detections: int
    confidence_threshold: float
    iou_threshold: float


@dataclass
class ModelConfig:
    """
    Полный конфиг ONNX-модели
    """

    model_name: str
    task_type: str
    model_path: str
    input: ModelInputConfig
    output: ModelOutputConfig
    postprocess: ModelPostprocessConfig
    classes: List[str]


@dataclass
class RawPrediction:
    """
    Сырой выход модели после ONNX Runtime
    """

    outputs: List[Any]


@dataclass
class ModelInfo:
    """
    Краткая информация о загруженной модели
    """

    model_name: str
    model_path: str
    input_name: str
    output_names: List[str]
    input_shape: Optional[Tuple[int, ...]] = None
    output_shapes: Optional[List[Tuple[int, ...]]] = None
