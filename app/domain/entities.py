from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]


@dataclass
class FrameResult:
    frame: np.ndarray
    detections: list[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    fps: float = 0.0
    frame_index: int = 0
    timestamp_sec: float = 0.0


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    models_dir: str
    model_config: str
    videos_dir: str
    default_video: str
    logs_dir: str
    results_dir: str
    default_confidence_threshold: float
    default_iou_threshold: float
    default_frame_skip: int
    device: str


@dataclass(frozen=True)
class ModelInputConfig:
    width: int
    height: int
    channels: int
    input_name: str
    color_format: str
    normalize: bool
    scale: float
    mean: list[float]
    std: list[float]


@dataclass(frozen=True)
class ModelOutputConfig:
    output_names: list[str]
    format: str


@dataclass(frozen=True)
class ModelPostprocessConfig:
    max_detections: int
    confidence_threshold: float
    iou_threshold: float


@dataclass(frozen=True)
class ModelConfig:
    model_name: str
    task_type: str
    model_path: str
    input: ModelInputConfig
    output: ModelOutputConfig
    postprocess: ModelPostprocessConfig
    classes: list[str]


@dataclass(frozen=True)
class RawPrediction:
    outputs: list[np.ndarray]


@dataclass(frozen=True)
class ModelInfo:
    model_name: str
    model_path: str
    input_name: str
    output_names: list[str]
    input_shape: Optional[tuple[int, ...]] = None
    output_shapes: Optional[list[tuple[int, ...]]] = None


@dataclass
class DetectionEvent:
    event_id: int
    class_ids: list[int]
    class_names: list[str]
    frame_index: int
    timestamp_sec: float
    image_path: str
    bboxes: list[tuple[int, int, int, int]] = field(default_factory=list)


@dataclass
class SessionSummary:
    session_id: str
    video_path: str
    started_at: str
    finished_at: Optional[str] = None
    total_detection_events: int = 0
    class_counts: dict[str, int] = field(default_factory=dict)
    events: list[DetectionEvent] = field(default_factory=list)
