import time
from typing import Any

import numpy as np

from app.inference.detector import OnnxDetector
from app.processing.drawing import draw_all
from app.inference.postprocess import get_postprocessor
from app.domain.entities import FrameResult, ModelConfig


class FrameProcessor:
    """
    Обрабатывает один кадр целиком:
    detector -> postprocess -> drawing
    """

    def __init__(
        self,
        model_config: ModelConfig,
        device: str = "cpu",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        draw_enabled: bool = True,
    ):
        self.model_config = model_config
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.draw_enabled = draw_enabled
        self.enabled_class_ids = set(range(len(self.model_config.classes)))

        self.detector = OnnxDetector(
            model_config=self.model_config,
            device=self.device,
        )
        self.postprocessor = get_postprocessor(self.model_config)

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        self.enabled_class_ids = set(class_ids)

    def set_confidence_threshold(self, value: float) -> None:
        self.confidence_threshold = float(value)

    def set_iou_threshold(self, value: float) -> None:
        self.iou_threshold = float(value)

    def set_draw_enabled(self, enabled: bool) -> None:
        self.draw_enabled = bool(enabled)

    def process_frame(self, frame: np.ndarray) -> FrameResult:
        """
        Полная обработка одного кадра
        """
        if frame is None:
            raise ValueError("Получен пустой кадр для обработки")

        total_start = time.perf_counter()

        infer_start = time.perf_counter()
        raw_outputs, preprocess_meta = self.detector.predict_raw(frame)
        inference_time_ms = (time.perf_counter() - infer_start) * 1000.0

        detections = self.postprocessor.process(
            raw_outputs=raw_outputs,
            original_width=frame.shape[1],
            original_height=frame.shape[0],
            confidence_threshold=self.confidence_threshold,
            iou_threshold=self.iou_threshold,
            preprocess_meta=preprocess_meta,
        )

        detections = [
            det for det in detections if det.class_id in self.enabled_class_ids
        ]

        if self.draw_enabled:
            output_frame = draw_all(
                frame=frame,
                detections=detections,
                model_name=self.model_config.model_name,
                fps=None,
                inference_time_ms=inference_time_ms,
                device=self.device,
            )
        else:
            output_frame = frame.copy()

        total_time_s = time.perf_counter() - total_start
        fps = 1.0 / total_time_s if total_time_s > 0 else 0.0

        return FrameResult(
            frame=output_frame,
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=fps,
        )

    def process_frame_without_drawing(self, frame: np.ndarray) -> FrameResult:
        if frame is None:
            raise ValueError("Получен пустой кадр для обработки")

        total_start = time.perf_counter()

        infer_start = time.perf_counter()
        raw_outputs, preprocess_meta = self.detector.predict_raw(frame)
        inference_time_ms = (time.perf_counter() - infer_start) * 1000.0

        detections = self.postprocessor.process(
            raw_outputs=raw_outputs,
            original_width=frame.shape[1],
            original_height=frame.shape[0],
            confidence_threshold=self.confidence_threshold,
            iou_threshold=self.iou_threshold,
            preprocess_meta=preprocess_meta,
        )

        detections = [
            det for det in detections if det.class_id in self.enabled_class_ids
        ]

        total_time_s = time.perf_counter() - total_start
        fps = 1.0 / total_time_s if total_time_s > 0 else 0.0

        return FrameResult(
            frame=frame.copy(),
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=fps,
        )

    def get_runtime_info(self) -> dict[str, Any]:
        return {
            "model_name": self.model_config.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "runtime": self.detector.get_runtime_info(),
        }

    def draw_existing_detections(
        self,
        frame,
        detections,
        inference_time_ms: float | None = None,
        fps: float | None = None,
    ):
        if frame is None:
            raise ValueError("Получен пустой кадр для отрисовки")

        if self.draw_enabled:
            output_frame = draw_all(
                frame=frame,
                detections=detections,
                model_name=self.model_config.model_name,
                fps=fps,
                inference_time_ms=inference_time_ms,
                device=self.device,
            )
        else:
            output_frame = frame.copy()

        return FrameResult(
            frame=output_frame,
            detections=detections,
            inference_time_ms=inference_time_ms or 0.0,
            fps=fps or 0.0,
        )
