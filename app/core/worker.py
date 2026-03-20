import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from app.core.frame_processor import FrameProcessor
from app.core.video_source import VideoSource
from app.domain.entities import FrameResult, ModelConfig


class VideoProcessingWorker(QObject):
    """
    Worker для обработки видеопотока в отдельном потоке.

    Поддерживает:
    - запуск обработки
    - паузу
    - продолжение
    - завершение текущего сеанса анализа

    ВАЖНО:
    Worker управляет только обработкой внутри приложения,
    но не управляет внешним устройством и не может остановить ленту интроскопа.
    """

    result_ready = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        model_config: ModelConfig,
        device: str = "cpu",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        process_every_n_frames: int = 1,
        draw_enabled: bool = True,
    ):
        super().__init__()

        self.model_config = model_config
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.process_every_n_frames = max(1, int(process_every_n_frames))
        self.draw_enabled = draw_enabled
        self.enabled_class_ids = set(range(len(self.model_config.classes)))

        self.video_path: Optional[str] = None
        self.video_source: Optional[VideoSource] = None
        self.frame_processor: Optional[FrameProcessor] = None

        self._is_running = False
        self._is_paused = False
        self._finish_requested = False

        self._frame_index = 0
        self._last_result: Optional[FrameResult] = None

    def set_video_path(self, video_path: str) -> None:
        self.video_path = video_path

    def set_confidence_threshold(self, value: float) -> None:
        self.confidence_threshold = float(value)
        if self.frame_processor is not None:
            self.frame_processor.set_confidence_threshold(value)

    def set_iou_threshold(self, value: float) -> None:
        self.iou_threshold = float(value)
        if self.frame_processor is not None:
            self.frame_processor.set_iou_threshold(value)

    def set_process_every_n_frames(self, value: int) -> None:
        self.process_every_n_frames = max(1, int(value))

    def set_draw_enabled(self, enabled: bool) -> None:
        self.draw_enabled = bool(enabled)
        if self.frame_processor is not None:
            self.frame_processor.set_draw_enabled(enabled)

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        self.enabled_class_ids = set(class_ids)
        if self.frame_processor is not None:
            self.frame_processor.set_enabled_class_ids(class_ids)

    @Slot()
    def start(self) -> None:
        """
        Основной цикл обработки видео.
        """
        if not self.video_path:
            self.error_occurred.emit("Не указан путь к видео")
            self.finished.emit()
            return

        if not Path(self.video_path).exists():
            self.error_occurred.emit(f"Видео не найдено: {self.video_path}")
            self.finished.emit()
            return

        self._is_running = True
        self._is_paused = False
        self._finish_requested = False
        self._frame_index = 0
        self._last_result = None

        try:
            self.status_changed.emit("Инициализация обработчика")

            self.frame_processor = FrameProcessor(
                model_config=self.model_config,
                device=self.device,
                confidence_threshold=self.confidence_threshold,
                iou_threshold=self.iou_threshold,
                draw_enabled=self.draw_enabled,
            )

            self.video_source = VideoSource(self.video_path)
            self.video_source.open()

            source_info = self.video_source.get_source_info()
            self.status_changed.emit(
                f"Видео открыто: {source_info['width']}x{source_info['height']}, "
                f"fps={source_info['fps']:.2f}, frames={source_info['frame_count']}"
            )

            total_start_time = time.perf_counter()

            while self._is_running:
                if self._finish_requested:
                    self.status_changed.emit("Сеанс анализа завершён")
                    break

                if self._is_paused:
                    time.sleep(0.03)
                    continue

                ok, frame = self.video_source.read()
                if not ok or frame is None:
                    self.status_changed.emit("Видео завершено")
                    break

                self._frame_index += 1
                should_process = self._frame_index % self.process_every_n_frames == 0

                if should_process:
                    current_result = self.frame_processor.process_frame(frame)
                    self._last_result = current_result
                else:
                    if self._last_result is not None:
                        current_result = self.frame_processor.draw_existing_detections(
                            frame=frame,
                            detections=self._last_result.detections,
                            inference_time_ms=self._last_result.inference_time_ms,
                        )
                    else:
                        current_result = (
                            self.frame_processor.process_frame_without_drawing(frame)
                        )

                elapsed_total = time.perf_counter() - total_start_time
                pipeline_fps = (
                    self._frame_index / elapsed_total if elapsed_total > 0 else 0.0
                )
                current_result.fps = pipeline_fps

                self.result_ready.emit(current_result)

            self._cleanup()
            self._is_running = False
            self._is_paused = False
            self.finished.emit()

        except Exception as e:
            self._cleanup()
            self._is_running = False
            self._is_paused = False
            self.error_occurred.emit(str(e))
            self.finished.emit()

    @Slot()
    def pause(self) -> None:
        """
        Приостановить обработку внутри приложения.
        """
        if not self._is_running:
            return

        if self._is_paused:
            return

        self._is_paused = True
        self.status_changed.emit("Обработка приостановлена")

    @Slot()
    def resume(self) -> None:
        """
        Продолжить обработку внутри приложения.
        """
        if not self._is_running:
            return

        if not self._is_paused:
            return

        self._is_paused = False
        self.status_changed.emit("Обработка продолжена")

    @Slot()
    def finish_processing(self) -> None:
        """
        Завершить текущий сеанс анализа.
        Освобождает видеоисточник и завершает цикл обработки.

        Это НЕ команда остановки ленты интроскопа.
        """
        if not self._is_running:
            return

        self._finish_requested = True
        self._is_paused = False
        self.status_changed.emit("Запрошено завершение сеанса анализа")

    @Slot()
    def stop(self) -> None:
        """
        Псевдоним для завершения текущего сеанса анализа.
        Нужен для совместимости с UI.
        """
        self.finish_processing()

    def is_running(self) -> bool:
        return self._is_running

    def is_paused(self) -> bool:
        return self._is_paused

    def _cleanup(self) -> None:
        if self.video_source is not None:
            self.video_source.release()
            self.video_source = None
