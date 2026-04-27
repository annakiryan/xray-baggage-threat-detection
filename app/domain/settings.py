from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InterfaceSettings:
    theme_key: str = "dark"
    ui_scale: int = 100
    bbox_color_key: str = "blue"
    bbox_thickness: int = 2


@dataclass
class InferenceSettings:
    device: str = "cpu"
    confidence_threshold: float = 0.4
    iou_threshold: float = 0.5
    frame_skip: int = 1

    def __post_init__(self) -> None:
        self.device = str(self.device).lower()
        self.confidence_threshold = float(self.confidence_threshold)
        self.iou_threshold = float(self.iou_threshold)
        self.frame_skip = max(1, int(self.frame_skip))


@dataclass
class DrawingSettings:
    enabled: bool = True
    box_color: tuple[int, int, int] = field(default_factory=lambda: (228, 107, 43))
    box_thickness: int = 2

    def __post_init__(self) -> None:
        self.enabled = bool(self.enabled)
        self.box_thickness = max(1, int(self.box_thickness))


@dataclass
class StorageSettings:
    default_video_path: str | Path | None = None
    logs_dir: str | Path = "logs"
    results_dir: str | Path = "results"

    def __post_init__(self) -> None:
        self.default_video_path = (
            Path(self.default_video_path) if self.default_video_path else None
        )
        self.logs_dir = Path(self.logs_dir)
        self.results_dir = Path(self.results_dir)


UI_SCALE_OPTIONS = [(value, f"{value}%") for value in range(80, 126, 5)]

BBOX_COLOR_OPTIONS = [
    ("blue", "Синий", "#0059FF"),
    ("green", "Зелёный", "#1DCB4C"),
    ("yellow", "Жёлтый", "#FFD452"),
    ("red", "Красный", "#C92822"),
]

BBOX_THICKNESS_OPTIONS = [1, 2, 3, 4, 5, 6]


def get_bbox_color_hex(color_key: str) -> str:
    for key, _, color_hex in BBOX_COLOR_OPTIONS:
        if key == color_key:
            return color_hex

    return next(color_hex for key, _, color_hex in BBOX_COLOR_OPTIONS if key == "blue")
