import time
from typing import Any, Optional

import numpy as np

from app.domain.entities import Detection, FrameResult, ModelConfig
from app.domain.settings import DrawingSettings, InferenceSettings
from app.inference.detector import OnnxDetector
from app.inference.postprocess import get_postprocessor
from app.processing.drawing import DEFAULT_BOX_COLOR, draw_all


class FrameProcessor:
    def __init__(
        self,
        model_config: ModelConfig,
        inference_settings: InferenceSettings | None = None,
        drawing_settings: DrawingSettings | None = None,
        detector: Optional[OnnxDetector] = None,
        postprocessor: Optional[Any] = None,
    ):
        self.model_config = model_config
        self.inference_settings = inference_settings or InferenceSettings()
        self.drawing_settings = drawing_settings or DrawingSettings(
            box_color=DEFAULT_BOX_COLOR
        )

        self.enabled_class_ids = set(range(len(self.model_config.classes)))

        self.detector = detector or OnnxDetector(
            model_config=self.model_config,
            device=self.device,
        )
        self.postprocessor = postprocessor or get_postprocessor(self.model_config)

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        self.enabled_class_ids = set(class_ids)

    def set_confidence_threshold(self, value: float) -> None:
        self.inference_settings.confidence_threshold = float(value)

    def set_iou_threshold(self, value: float) -> None:
        self.inference_settings.iou_threshold = float(value)

    def set_draw_enabled(self, enabled: bool) -> None:
        self.drawing_settings.enabled = bool(enabled)

    def set_box_color(self, color: tuple[int, int, int]) -> None:
        self.drawing_settings.box_color = color

    def set_box_thickness(self, thickness: int) -> None:
        self.drawing_settings.box_thickness = max(1, int(thickness))

    def process_frame(self, frame: np.ndarray) -> FrameResult:
        self._validate_frame(frame)

        total_start = time.perf_counter()

        detections, inference_time_ms = self._run_detection(frame)
        output_frame = self._prepare_output_frame(
            frame=frame,
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=None,
        )

        total_time_s = time.perf_counter() - total_start
        fps = 1.0 / total_time_s if total_time_s > 0 else 0.0

        return FrameResult(
            frame=output_frame,
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=fps,
        )

    def process_frame_without_drawing(self, frame: np.ndarray) -> FrameResult:
        self._validate_frame(frame)

        total_start = time.perf_counter()

        detections, inference_time_ms = self._run_detection(frame)

        total_time_s = time.perf_counter() - total_start
        fps = 1.0 / total_time_s if total_time_s > 0 else 0.0

        return FrameResult(
            frame=frame.copy(),
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=fps,
        )

    def draw_existing_detections(
        self,
        frame: np.ndarray,
        detections: list[Detection],
        inference_time_ms: float | None = None,
        fps: float | None = None,
    ) -> FrameResult:
        self._validate_frame(frame)

        output_frame = self._prepare_output_frame(
            frame=frame,
            detections=detections,
            inference_time_ms=inference_time_ms,
            fps=fps,
        )

        return FrameResult(
            frame=output_frame,
            detections=list(detections),
            inference_time_ms=float(inference_time_ms or 0.0),
            fps=float(fps or 0.0),
        )

    def get_runtime_info(self) -> dict[str, Any]:
        return {
            "model_name": self.model_config.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "draw_enabled": self.draw_enabled,
            "enabled_class_ids": sorted(self.enabled_class_ids),
            "runtime": self.detector.get_runtime_info(),
        }

    @property
    def device(self) -> str:
        return self.inference_settings.device

    @property
    def confidence_threshold(self) -> float:
        return self.inference_settings.confidence_threshold

    @property
    def iou_threshold(self) -> float:
        return self.inference_settings.iou_threshold

    @property
    def draw_enabled(self) -> bool:
        return self.drawing_settings.enabled

    @property
    def box_color(self) -> tuple[int, int, int]:
        return self.drawing_settings.box_color

    @property
    def box_thickness(self) -> int:
        return self.drawing_settings.box_thickness

    def _run_detection(self, frame: np.ndarray) -> tuple[list[Detection], float]:
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

        detections = self._filter_detections_by_enabled_classes(detections)

        return detections, inference_time_ms

    def _filter_detections_by_enabled_classes(
        self,
        detections: list[Detection],
    ) -> list[Detection]:
        return [det for det in detections if det.class_id in self.enabled_class_ids]

    def _prepare_output_frame(
        self,
        frame: np.ndarray,
        detections: list[Detection],
        inference_time_ms: float | None,
        fps: float | None,
    ) -> np.ndarray:
        if not self.draw_enabled:
            return frame.copy()

        return draw_all(
            frame=frame,
            detections=detections,
            model_name=self.model_config.model_name,
            fps=fps,
            inference_time_ms=inference_time_ms,
            device=self.device,
            box_color=self.box_color,
            box_thickness=self.box_thickness,
        )

    @staticmethod
    def _validate_frame(frame: np.ndarray) -> None:
        if frame is None:
            raise ValueError("Получен пустой кадр для обработки")

        if not isinstance(frame, np.ndarray):
            raise TypeError(f"Ожидался numpy.ndarray, получено: {type(frame).__name__}")

        if frame.ndim < 2:
            raise ValueError("Некорректный формат кадра: ожидалось изображение")
