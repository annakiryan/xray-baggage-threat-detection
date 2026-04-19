from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.processing.drawing import draw_text_pil


class CaptureService:
    @staticmethod
    def ensure_results_dir(results_dir: str = "results") -> Path:
        path = Path(results_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def add_timestamp_overlay(frame: np.ndarray, timestamp_text: str) -> np.ndarray:
        if frame is None:
            raise ValueError("Пустой кадр для сохранения")

        result = frame.copy()
        height, width = result.shape[:2]

        bar_height = 46
        cv2.rectangle(result, (0, height - bar_height), (width, height), (30, 30, 30), -1)

        return draw_text_pil(
            frame=result,
            text=timestamp_text,
            position=(12, height - 36),
            font_size=24,
            text_color=(255, 255, 255),
        )

    @staticmethod
    def save_frame(frame: np.ndarray, results_dir: str = "results") -> Path:
        if frame is None:
            raise ValueError("Нет кадра для сохранения")

        results_path = CaptureService.ensure_results_dir(results_dir)

        now = datetime.now()
        timestamp_for_text = now.strftime("%d.%m.%Y %H:%M:%S")
        timestamp_for_filename = now.strftime("%Y-%m-%d_%H-%M-%S")

        frame_with_timestamp = CaptureService.add_timestamp_overlay(
            frame,
            f"Дата и время: {timestamp_for_text}",
        )

        save_path = results_path / f"capture_{timestamp_for_filename}.jpg"

        ok = cv2.imwrite(str(save_path), frame_with_timestamp)
        if not ok:
            raise RuntimeError(f"Не удалось сохранить кадр: {save_path}")

        return save_path