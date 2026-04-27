from pathlib import Path
from threading import Thread
from typing import Optional
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from app.domain.entities import FrameResult, ModelConfig
from app.domain.settings import DrawingSettings, InferenceSettings, StorageSettings
from app.logging import LoggerService
from app.processing.video_processing_worker import VideoProcessingWorker
from app.video.capture_service import CaptureService
from app.session.session_results_service import SessionResultsService, SessionStructure
from app.processing.detection_event_manager import DetectionEventManager
from app.processing.drawing import hex_to_bgr


@dataclass
class CurrentSessionArtifacts:
    session: SessionStructure
    detection_event_manager: DetectionEventManager


class AnalysisSession(QObject):
    result_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    session_started = Signal()
    session_finished = Signal()

    def __init__(
        self,
        model_config: ModelConfig,
        storage_settings: StorageSettings,
        inference_settings: InferenceSettings | None = None,
        drawing_settings: DrawingSettings | None = None,
    ):
        super().__init__()

        self.model_config = model_config
        self.storage_settings = storage_settings
        self.inference_settings = inference_settings or InferenceSettings()
        self.drawing_settings = drawing_settings or DrawingSettings()
        self.device = self.inference_settings.device
        self.confidence_threshold = self.inference_settings.confidence_threshold
        self.iou_threshold = self.inference_settings.iou_threshold
        self.frame_skip = self.inference_settings.frame_skip
        self.draw_enabled = self.drawing_settings.enabled
        self.enabled_class_ids = set(range(len(self.model_config.classes)))
        self.box_color = self.drawing_settings.box_color
        self.box_thickness = self.drawing_settings.box_thickness

        self.video_path: Optional[Path] = self.storage_settings.default_video_path
        self.results_dir = self.storage_settings.results_dir

        self._worker: Optional[VideoProcessingWorker] = None
        self._thread: Optional[Thread] = None

        self._is_running = False
        self._is_paused = False

        self.logger = LoggerService.get_logger(
            self.__class__.__name__,
            logs_dir=self.storage_settings.logs_dir,
        )

        self.current_artifacts: Optional[CurrentSessionArtifacts] = None

    def set_video_path(self, video_path: str | Path) -> None:
        self.video_path = Path(video_path)

    def set_confidence_threshold(self, value: float) -> None:
        self.confidence_threshold = float(value)
        self.inference_settings.confidence_threshold = self.confidence_threshold
        if self._worker is not None:
            self._worker.set_confidence_threshold(value)
        self.logger.info(
            "Изменён confidence_threshold: %.2f", self.confidence_threshold
        )

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        self.enabled_class_ids = set(class_ids)

        if self._worker is not None:
            self._worker.set_enabled_class_ids(class_ids)

        self.logger.info(
            "Изменён набор отображаемых классов: %s",
            sorted(self.enabled_class_ids),
        )

    def set_bbox_color(self, color: tuple[int, int, int]) -> None:
        self.box_color = color
        self.drawing_settings.box_color = color

        if self._worker is not None:
            self._worker.set_box_color(color)

    def set_bbox_color_hex(self, color_hex: str) -> None:
        self.set_bbox_color(hex_to_bgr(color_hex))

    def set_bbox_thickness(self, thickness: int) -> None:
        self.box_thickness = max(1, int(thickness))
        self.drawing_settings.box_thickness = self.box_thickness

        if self._worker is not None:
            self._worker.set_box_thickness(self.box_thickness)

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

        if self.video_path is None:
            self._emit_error("Не указан путь к видео")
            return

        if not self.video_path.exists():
            self._emit_error(f"Видео не найдено: {self.video_path}")
            return

        self.current_artifacts = self._create_session_artifacts()

        self._worker = VideoProcessingWorker(
            model_config=self.model_config,
            inference_settings=self.inference_settings,
            drawing_settings=self.drawing_settings,
            on_result_ready=self._handle_result_ready,
            on_status_changed=self._handle_status_changed,
            on_error=self._handle_error_occurred,
            on_finished=self._handle_worker_finished,
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

        if self.current_artifacts is None:
            raise RuntimeError("Сеанс анализа не запущен")

        return CaptureService.save_frame(
            frame=frame,
            results_dir=str(self.current_artifacts.session.manual_captures_dir),
        )

    def _handle_result_ready(self, result: FrameResult) -> None:
        if self.current_artifacts is not None:
            self.current_artifacts.detection_event_manager.process_frame_result(result)

        self.result_ready.emit(result)

    def _handle_status_changed(self, text: str) -> None:
        self.status_changed.emit(text)

    def _handle_error_occurred(self, message: str) -> None:
        self._report_error(message)

    def _emit_error(self, message: str) -> None:
        self._report_error(message)

    def _report_error(self, message: str) -> None:
        self.logger.error("Ошибка: %s", message)
        self.error_occurred.emit(message)

    def _handle_worker_finished(self) -> None:
        if self.current_artifacts is not None:
            SessionResultsService.finalize_summary(
                summary=self.current_artifacts.session.summary,
                summary_path=self.current_artifacts.session.summary_path,
            )

        self._worker = None
        self._thread = None
        self._is_running = False
        self._is_paused = False
        self.current_artifacts = None

        self.logger.info("Сеанс анализа завершён")
        self.session_finished.emit()

    def _create_session_artifacts(self) -> CurrentSessionArtifacts:
        if self.video_path is None:
            raise RuntimeError("Не указан путь к видео")

        session_structure = SessionResultsService.create_session_structure(
            results_dir=self.results_dir,
            video_path=self.video_path,
        )

        detection_event_manager = DetectionEventManager(
            session_summary=session_structure.summary,
            summary_path=session_structure.summary_path,
            detections_dir=session_structure.detections_dir,
        )

        return CurrentSessionArtifacts(
            session=session_structure,
            detection_event_manager=detection_event_manager,
        )

    def change_video_path(self, video_path: str | Path) -> None:
        new_video_path = Path(video_path)

        if self.video_path is not None:
            try:
                if self.video_path.resolve() == new_video_path.resolve():
                    return
            except OSError:
                if self.video_path == new_video_path:
                    return

        if self._is_running and self._worker is not None:
            self.logger.info("Запрошено завершение сеанса из-за смены видео")
            self._worker.stop()
            self._is_paused = False

        self.video_path = new_video_path
