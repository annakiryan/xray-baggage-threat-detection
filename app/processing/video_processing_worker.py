import time
import traceback
from pathlib import Path
from threading import Event, Lock
from typing import Callable, Optional

from app.domain.entities import FrameResult, ModelConfig
from app.domain.settings import DrawingSettings, InferenceSettings
from app.processing.frame_processor import FrameProcessor
from app.video.video_source import VideoSource


class VideoProcessingWorker:
    def __init__(
        self,
        model_config: ModelConfig,
        inference_settings: InferenceSettings,
        drawing_settings: DrawingSettings,
        on_result_ready: Optional[Callable[[FrameResult], None]] = None,
        on_status_changed: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        self.model_config = model_config
        self.inference_settings = inference_settings
        self.drawing_settings = drawing_settings

        self.on_result_ready = on_result_ready
        self.on_status_changed = on_status_changed
        self.on_error = on_error
        self.on_finished = on_finished

        self.enabled_class_ids = set(range(len(self.model_config.classes)))

        self.video_path: Optional[str] = None
        self.video_source: Optional[VideoSource] = None
        self.frame_processor: Optional[FrameProcessor] = None

        self._running = False
        self._pause_event = Event()
        self._stop_event = Event()
        self._settings_lock = Lock()

        self._frame_index = 0
        self._last_result: Optional[FrameResult] = None

    def set_video_path(self, video_path: str | Path) -> None:
        self.video_path = str(video_path)

    def set_confidence_threshold(self, value: float) -> None:
        with self._settings_lock:
            self.inference_settings.confidence_threshold = float(value)
            if self.frame_processor is not None:
                self.frame_processor.set_confidence_threshold(value)

    def set_iou_threshold(self, value: float) -> None:
        with self._settings_lock:
            self.inference_settings.iou_threshold = float(value)
            if self.frame_processor is not None:
                self.frame_processor.set_iou_threshold(value)

    def set_draw_enabled(self, enabled: bool) -> None:
        with self._settings_lock:
            self.drawing_settings.enabled = bool(enabled)
            if self.frame_processor is not None:
                self.frame_processor.set_draw_enabled(enabled)

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        with self._settings_lock:
            self.enabled_class_ids = set(class_ids)
            if self.frame_processor is not None:
                self.frame_processor.set_enabled_class_ids(class_ids)

    def set_box_color(self, color: tuple[int, int, int]) -> None:
        with self._settings_lock:
            self.drawing_settings.box_color = color
            if self.frame_processor is not None:
                self.frame_processor.set_box_color(color)

    def set_box_thickness(self, thickness: int) -> None:
        with self._settings_lock:
            self.drawing_settings.box_thickness = max(1, int(thickness))
            if self.frame_processor is not None:
                self.frame_processor.set_box_thickness(
                    self.drawing_settings.box_thickness
                )

    def pause(self) -> None:
        if not self._running:
            return
        if self._pause_event.is_set():
            return

        self._pause_event.set()
        self._emit_status("Обработка приостановлена")

    def resume(self) -> None:
        if not self._running:
            return
        if not self._pause_event.is_set():
            return

        self._pause_event.clear()
        self._emit_status("Обработка продолжена")

    def stop(self) -> None:
        if not self._running:
            return

        self._stop_event.set()
        self._pause_event.clear()
        self._emit_status("Запрошено завершение сеанса анализа")

    def run(self) -> None:
        try:
            self._prepare_run()
            self._run_loop()
        except Exception as e:
            error_text = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            self._emit_error(error_text)
        finally:
            self._cleanup()
            self._emit_finished()

    def _prepare_run(self) -> None:
        if not self.video_path:
            raise ValueError("Не указан путь к видео")

        path = Path(self.video_path)
        if not path.exists():
            raise FileNotFoundError(f"Видео не найдено: {self.video_path}")

        self._running = True
        self._pause_event.clear()
        self._stop_event.clear()
        self._frame_index = 0
        self._last_result = None

        self._emit_status("Инициализация обработчика")

        self.frame_processor = FrameProcessor(
            model_config=self.model_config,
            inference_settings=self.inference_settings,
            drawing_settings=self.drawing_settings,
        )
        self.frame_processor.set_enabled_class_ids(self.enabled_class_ids)

        self.video_source = VideoSource(self.video_path)
        self.video_source.open()

        self.source_fps = self.video_source.get_fps()
        if self.source_fps <= 0:
            self.source_fps = 25.0

        self._emit_status("Идёт анализ")

    def _run_loop(self) -> None:
        assert self.video_source is not None
        assert self.frame_processor is not None

        total_start_time = time.perf_counter()

        while self._running:
            if self._stop_event.is_set():
                self._emit_status("Сеанс анализа завершён")
                break

            if self._pause_event.is_set():
                time.sleep(0.03)
                continue

            ok, frame = self.video_source.read()
            if not ok or frame is None:
                self._emit_status("Видео завершено")
                break

            self._frame_index += 1
            current_result = self._process_frame(frame)

            elapsed_total = time.perf_counter() - total_start_time
            pipeline_fps = (
                self._frame_index / elapsed_total if elapsed_total > 0 else 0.0
            )
            current_result.fps = pipeline_fps
            current_result.frame_index = self._frame_index
            current_result.timestamp_sec = self._frame_index / self.source_fps

            self._emit_result(current_result)

    def _process_frame(self, frame) -> FrameResult:
        assert self.frame_processor is not None

        with self._settings_lock:
            should_run_inference = (
                self._frame_index % self.inference_settings.frame_skip == 0
            )

            if should_run_inference:
                result = self.frame_processor.process_frame(frame)
                self._last_result = result
                return result

            if self._last_result is not None:
                return self.frame_processor.draw_existing_detections(
                    frame=frame,
                    detections=self._last_result.detections,
                    inference_time_ms=self._last_result.inference_time_ms,
                )

            return self.frame_processor.process_frame_without_drawing(frame)

    def _cleanup(self) -> None:
        if self.video_source is not None:
            self.video_source.release()
            self.video_source = None

        self.frame_processor = None
        self._running = False
        self._pause_event.clear()
        self._stop_event.clear()

    def _emit_result(self, result: FrameResult) -> None:
        if self.on_result_ready is not None:
            self.on_result_ready(result)

    def _emit_status(self, text: str) -> None:
        if self.on_status_changed is not None:
            self.on_status_changed(text)

    def _emit_error(self, text: str) -> None:
        if self.on_error is not None:
            self.on_error(text)

    def _emit_finished(self) -> None:
        if self.on_finished is not None:
            self.on_finished()
