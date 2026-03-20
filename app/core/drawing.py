import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.domain.entities import Detection


def draw_detections(
    frame: np.ndarray,
    detections: list[Detection],
    box_color: tuple[int, int, int] = (0, 255, 0),
    box_thickness: int = 2,
    font_scale: float = 0.6,
    font_thickness: int = 2,
) -> np.ndarray:
    """
    Рисует детекции на копии кадра и возвращает результат.

    Parameters
    ----------
    frame : np.ndarray
        Исходный кадр в формате OpenCV (BGR).
    detections : list[Detection]
        Список детекций.
    box_color : tuple[int, int, int]
        Цвет бокса в формате BGR.
    box_thickness : int
        Толщина линии бокса.
    font_scale : float
        Размер шрифта подписи.
    font_thickness : int
        Толщина шрифта подписи.
    """
    if frame is None:
        raise ValueError("Получен пустой кадр для отрисовки")

    result = frame.copy()

    for det in detections:
        x1, y1, x2, y2 = det.bbox
        label = f"{det.class_name}: {det.confidence:.2f}"

        # Бокс
        cv2.rectangle(result, (x1, y1), (x2, y2), box_color, box_thickness)

        # Размер текста
        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            font_thickness,
        )

        # Координаты фона для текста
        text_x = x1
        text_y = max(y1 - 10, text_height + 10)

        bg_x1 = text_x
        bg_y1 = text_y - text_height - baseline
        bg_x2 = text_x + text_width + 6
        bg_y2 = text_y + baseline

        # Фон под текст
        cv2.rectangle(result, (bg_x1, bg_y1), (bg_x2, bg_y2), box_color, -1)

        # Текст
        result = draw_text_pil(
            frame=result,
            text=label,
            position=(text_x + 3, bg_y1),
            font_size=20,
            text_color=(0, 0, 0),
        )

    return result


def draw_status_bar(
    frame: np.ndarray,
    model_name: str | None = None,
    fps: float | None = None,
    inference_time_ms: float | None = None,
    device: str | None = None,
) -> np.ndarray:
    """
    Рисует сверху служебную строку со статусом.

    Parameters
    ----------
    frame : np.ndarray
        Исходный кадр.
    model_name : str | None
        Имя модели.
    fps : float | None
        FPS.
    inference_time_ms : float | None
        Время инференса в миллисекундах.
    device : str | None
        Устройство выполнения, например 'cpu' или 'cuda'.
    """
    if frame is None:
        raise ValueError("Получен пустой кадр для отрисовки status bar")

    result = frame.copy()
    h, w = result.shape[:2]

    parts = []
    if model_name:
        parts.append(f"Model: {model_name}")
    if device:
        parts.append(f"Device: {device}")
    if fps is not None:
        parts.append(f"FPS: {fps:.1f}")
    if inference_time_ms is not None:
        parts.append(f"Inference: {inference_time_ms:.1f} ms")

    if not parts:
        return result

    text = " | ".join(parts)

    bar_height = 36
    cv2.rectangle(result, (0, 0), (w, bar_height), (40, 40, 40), -1)

    cv2.putText(
        result,
        text,
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return result


def draw_all(
    frame: np.ndarray,
    detections: list[Detection],
    model_name: str | None = None,
    fps: float | None = None,
    inference_time_ms: float | None = None,
    device: str | None = None,
) -> np.ndarray:
    """
    Полная отрисовка:
    1. статусная строка
    2. боксы и подписи
    """
    result = draw_status_bar(
        frame=frame,
        model_name=model_name,
        fps=fps,
        inference_time_ms=inference_time_ms,
        device=device,
    )
    result = draw_detections(result, detections)
    return result


def draw_text_pil(
    frame: np.ndarray,
    text: str,
    position: tuple[int, int],
    font_size: int = 20,
    text_color: tuple[int, int, int] = (255, 255, 255),
    font_path: str = "C:/Windows/Fonts/arial.ttf",
) -> np.ndarray:
    """
    Рисует текст с поддержкой кириллицы через Pillow.
    position задается в координатах OpenCV.
    text_color задается в BGR, как в OpenCV.
    """
    if frame is None:
        raise ValueError("Получен пустой кадр для draw_text_pil")

    # BGR -> RGB
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    draw = ImageDraw.Draw(pil_image)

    font = ImageFont.truetype(font_path, font_size)

    rgb_text_color = (text_color[2], text_color[1], text_color[0])
    draw.text(position, text, font=font, fill=rgb_text_color)

    # RGB -> BGR
    result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return result
