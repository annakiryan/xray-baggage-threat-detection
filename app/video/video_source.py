from pathlib import Path
from typing import Optional

import cv2
import numpy as np


class VideoSource:

    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened: bool = False

    def open(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Видео не найдено: {self.source_path}")

        self.cap = cv2.VideoCapture(str(self.source_path))

        if not self.cap.isOpened():
            self.cap = None
            raise RuntimeError(f"Не удалось открыть видеоисточник: {self.source_path}")

        self.is_opened = True

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        success, frame = self.cap.read()

        if not success:
            return False, None

        return True, frame

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.is_opened = False

    def reset(self) -> None:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def get_fps(self) -> float:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return float(fps) if fps > 0 else 0.0

    def get_width(self) -> int:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_height(self) -> int:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame_count(self) -> int:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_current_frame_index(self) -> int:
        if not self.is_opened or self.cap is None:
            raise RuntimeError("Видеоисточник не открыт")

        return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))

    def get_source_info(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "fps": self.get_fps(),
            "width": self.get_width(),
            "height": self.get_height(),
            "frame_count": self.get_frame_count(),
        }

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
