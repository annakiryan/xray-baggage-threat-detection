from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.domain.entities import Detection


DEFAULT_BOX_COLOR = (0, 255, 0)
DEFAULT_TEXT_COLOR_ON_BOX = (0, 0, 0)


def draw_all(
    frame: np.ndarray,
    detections: list[Detection],
    model_name: str | None = None,
    fps: float | None = None,
    inference_time_ms: float | None = None,
    device: str | None = None,
) -> np.ndarray:
    _validate_frame(frame)
    return draw_detections(frame, detections)


def draw_detections(
    frame: np.ndarray,
    detections: list[Detection],
    box_color: tuple[int, int, int] = DEFAULT_BOX_COLOR,
    box_thickness: int = 2,
    font_scale: float = 0.6,
    font_thickness: int = 2,
    label_font_size: int = 20,
) -> np.ndarray:
    _validate_frame(frame)

    result = frame.copy()

    for det in detections:
        result = _draw_single_detection(
            frame=result,
            detection=det,
            box_color=box_color,
            box_thickness=box_thickness,
            font_scale=font_scale,
            font_thickness=font_thickness,
            label_font_size=label_font_size,
        )

    return result


def draw_text_pil(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    font_size: int = 20,
    text_color: tuple[int, int, int] = (255, 255, 255),
    font_path: str | None = None,
) -> np.ndarray:
    _validate_frame(frame)

    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    draw = ImageDraw.Draw(pil_image)

    font = _load_font(font_size=font_size, font_path=font_path)

    rgb_text_color = (text_color[2], text_color[1], text_color[0])
    draw.text(position, text, font=font, fill=rgb_text_color)

    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def _draw_single_detection(
    frame: np.ndarray,
    detection: Detection,
    box_color: tuple[int, int, int],
    box_thickness: int,
    font_scale: float,
    font_thickness: int,
    label_font_size: int,
) -> np.ndarray:
    result = frame.copy()

    x1, y1, x2, y2 = detection.bbox
    label = f"{detection.class_name}: {detection.confidence:.2f}"

    cv2.rectangle(result, (x1, y1), (x2, y2), box_color, box_thickness)

    text_rect = _compute_label_background_rect(
        label=label,
        anchor_x=x1,
        anchor_y=y1,
        font_scale=font_scale,
        font_thickness=font_thickness,
    )

    cv2.rectangle(
        result,
        (text_rect["bg_x1"], text_rect["bg_y1"]),
        (text_rect["bg_x2"], text_rect["bg_y2"]),
        box_color,
        -1,
    )

    result = draw_text_pil(
        frame=result,
        text=label,
        position=(text_rect["text_x"], text_rect["text_y"]),
        font_size=label_font_size,
        text_color=DEFAULT_TEXT_COLOR_ON_BOX,
    )

    return result


def _compute_label_background_rect(
    label: str,
    anchor_x: int,
    anchor_y: int,
    font_scale: float,
    font_thickness: int,
) -> dict[str, int]:
    (text_width, text_height), baseline = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        font_thickness,
    )

    text_x = anchor_x + 3
    text_y_base = max(anchor_y - 10, text_height + 10)

    bg_x1 = anchor_x
    bg_y1 = text_y_base - text_height - baseline
    bg_x2 = anchor_x + text_width + 6
    bg_y2 = text_y_base + baseline

    return {
        "bg_x1": bg_x1,
        "bg_y1": bg_y1,
        "bg_x2": bg_x2,
        "bg_y2": bg_y2,
        "text_x": text_x,
        "text_y": bg_y1,
    }


def _load_font(font_size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidate_paths = []

    if font_path:
        candidate_paths.append(font_path)

    candidate_paths.extend(
        [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    )

    for candidate in candidate_paths:
        try:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, font_size)
        except Exception:
            continue

    return ImageFont.load_default()


def _validate_frame(frame: Optional[np.ndarray]) -> None:
    if frame is None:
        raise ValueError("Получен пустой кадр для отрисовки")

    if not isinstance(frame, np.ndarray):
        raise TypeError(f"Ожидался numpy.ndarray, получено: {type(frame).__name__}")

    if frame.ndim < 2:
        raise ValueError("Некорректный формат кадра: ожидалось изображение")