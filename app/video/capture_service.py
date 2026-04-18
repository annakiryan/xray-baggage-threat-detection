from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class CaptureService:
    @staticmethod
    def ensure_results_dir(results_dir: str = "results") -> Path:
        path = Path(results_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _draw_text_pil(
        frame: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_size: int = 24,
        text_color: tuple[int, int, int] = (255, 255, 255),
        font_path: str = "C:/Windows/Fonts/arial.ttf",
    ) -> np.ndarray:
        if frame is None:
            raise ValueError("Пустой кадр для отрисовки текста")

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)

        font = ImageFont.truetype(font_path, font_size)

        # BGR -> RGB
        rgb_text_color = (text_color[2], text_color[1], text_color[0])
        draw.text(position, text, font=font, fill=rgb_text_color)

        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def add_timestamp_overlay(frame: np.ndarray, timestamp_text: str) -> np.ndarray:
        if frame is None:
            raise ValueError("Пустой кадр для сохранения")

        result = frame.copy()
        h, w = result.shape[:2]

        bar_height = 46
        cv2.rectangle(result, (0, h - bar_height), (w, h), (30, 30, 30), -1)

        result = CaptureService._draw_text_pil(
            result,
            timestamp_text,
            position=(12, h - 36),
            font_size=24,
            text_color=(255, 255, 255),
        )

        return result

    @staticmethod
    def save_frame(frame: np.ndarray, results_dir: str = "results") -> Path:
        if frame is None:
            raise ValueError("Нет кадра для сохранения")

        results_path = CaptureService.ensure_results_dir(results_dir)

        now = datetime.now()
        timestamp_for_text = now.strftime("%d.%m.%Y %H:%M:%S")
        timestamp_for_filename = now.strftime("%Y-%m-%d_%H-%M-%S")

        frame_with_timestamp = CaptureService.add_timestamp_overlay(
            frame, f"Дата и время: {timestamp_for_text}"
        )

        save_path = results_path / f"capture_{timestamp_for_filename}.jpg"

        ok = cv2.imwrite(str(save_path), frame_with_timestamp)
        if not ok:
            raise RuntimeError(f"Не удалось сохранить кадр: {save_path}")

        return save_path
