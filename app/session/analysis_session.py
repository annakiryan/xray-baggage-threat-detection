from pathlib import Path
from threading import Thread
from typing import Optional

from PySide6.QtCore import QObject, Signal

from app.domain.entities import FrameResult, ModelConfig
from app.logging import LoggerService
from app.processing.worker import VideoProcessingWorker
from app.video.capture_service import CaptureService


class AnalysisSession(QObject):
    result_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    session_started = Signal()
    session_finished = Signal()

    def __init__(
        self,
        default_video: str,
        logs_dir: str,
        results_dir: str,
        model_config: ModelConfig,
        device: str = "cpu",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        frame_skip: int = 1,
        draw_enabled: bool = True,
    ):
        super().__init__()

        self.model_config = model_config
        self.device = device
        self.confidence_threshold = float(confidence_threshold)
        self.iou_threshold = float(iou_threshold)
        self.frame_skip = max(1, int(frame_skip))
        self.draw_enabled = bool(draw_enabled)
        self.enabled_class_ids = set(range(len(self.model_config.classes)))

        self.video_path: Optional[str] = default_video
        self.results_dir = results_dir

        self._worker: Optional[VideoProcessingWorker] = None
        self._thread: Optional[Thread] = None

        self._is_running = False
        self._is_paused = False

        self.logger = LoggerService.get_logger(
            self.__class__.__name__,
            logs_dir=logs_dir,
        )

    def set_video_path(self, video_path: str) -> None:
        self.video_path = video_path

    def set_confidence_threshold(self, value: float) -> None:
        self.confidence_threshold = float(value)
        if self._worker is not None:
            self._worker.set_confidence_threshold(value)
        self.logger.info("Изменён confidence_threshold: %.2f", self.confidence_threshold)

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        self.enabled_class_ids = set(class_ids)

        if self._worker is not None:
            self._worker.set_enabled_class_ids(class_ids)

        self.logger.info(
            "Изменён набор отображаемых классов: %s",
            sorted(self.enabled_class_ids),
        )

    def get_enabled_class_ids(self) -> set[int]:
        return set(self.enabled_class_ids)

    def is_running(self) -> bool:
        return self._is_running

    def is_paused(self) -> bool:
        return self._is_paused

    def start(self) -> None:
        if self._is_running:
            self.status_changed.emit("Сеанс анализа уже запущен")
            return

        if not self.video_path:
            self._emit_error("Не указан путь к видео")
            return

        if not Path(self.video_path).exists():
            self._emit_error(f"Видео не найдено: {self.video_path}")
            return

        self._worker = VideoProcessingWorker(
            model_config=self.model_config,
            device=self.device,
            confidence_threshold=self.confidence_threshold,
            iou_threshold=self.iou_threshold,
            process_every_n_frames=self.frame_skip,
            draw_enabled=self.draw_enabled,
            on_result_ready=self._handle_result_ready,
            on_status_changed=self._handle_status_changed,
            on_error=self._handle_error_occurred,
            on_finished=self._on_worker_finished,
        )

        self._worker.set_video_path(self.video_path)
        self._worker.set_enabled_class_ids(self.enabled_class_ids)

        self._thread = Thread(target=self._worker.run, daemon=True)
        self._thread.start()

        self._is_running = True
        self._is_paused = False

        self.logger.info("Сеанс анализа запущен")
        self.session_started.emit()

    def pause(self) -> None:
        if not self._is_running or self._worker is None or self._is_paused:
            return

        self._worker.pause()
        self._is_paused = True

    def resume(self) -> None:
        if not self._is_running or self._worker is None or not self._is_paused:
            return

        self._worker.resume()
        self._is_paused = False

    def stop(self) -> None:
        if not self._is_running or self._worker is None:
            return

        self.logger.info("Сеанс анализа завершен")
        self._worker.stop()
        self._is_paused = False

    def capture_frame(self, frame) -> Path:
        if frame is None:
            raise ValueError("Нет кадра для сохранения")

        return CaptureService.save_frame(
            frame=frame,
            results_dir=self.results_dir,
        )

    def _handle_result_ready(self, result: FrameResult) -> None:
        self.result_ready.emit(result)

    def _handle_status_changed(self, text: str) -> None:
        self.status_changed.emit(text)

    def _handle_error_occurred(self, message: str) -> None:
        self.logger.error("Ошибка: %s", message)
        self.error_occurred.emit(message)

    def _emit_error(self, message: str) -> None:
        self.logger.error("Ошибка: %s", message)
        self.error_occurred.emit(message)

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._thread = None
        self._is_running = False
        self._is_paused = False
        self.logger.info("Сеанс анализа завершён")
        self.session_finished.emit()