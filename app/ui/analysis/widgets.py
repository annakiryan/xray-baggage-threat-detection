from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QFormLayout,
    QComboBox,
)


class SourceGroup(QGroupBox):
    video_selected = Signal(object)

    def __init__(
        self,
        videos: list[Path],
        default_video: str | Path | None = None,
    ):
        super().__init__("Источник видео")

        self.videos = videos

        self.video_combo = QComboBox()
        self.video_combo.setObjectName("videoCombo")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Видео"))
        layout.addWidget(self.video_combo)

        self._fill_videos(default_video)

        self.video_combo.currentIndexChanged.connect(self._on_video_changed)

    def _fill_videos(self, default_video: str | Path | None) -> None:
        self.video_combo.blockSignals(True)
        self.video_combo.clear()

        if not self.videos:
            self.video_combo.addItem("Видео не найдены", "")
            self.video_combo.setEnabled(False)
            self.video_combo.blockSignals(False)
            return

        default_name = Path(default_video).name.lower() if default_video else None
        default_index = 0

        for index, video_path in enumerate(self.videos):
            video_path = Path(video_path)
            self.video_combo.addItem(video_path.name, str(video_path.resolve()))

            if default_name and video_path.name.lower() == default_name:
                default_index = index

        self.video_combo.setCurrentIndex(default_index)
        self.video_combo.blockSignals(False)

    def _on_video_changed(self, index: int) -> None:
        video_path = self.video_combo.itemData(index)

        if video_path:
            self.video_selected.emit(Path(video_path))

    def selected_video_path(self) -> Path | None:
        value = self.video_combo.currentData()
        return Path(value) if value else None


class ControlGroup(QGroupBox):
    def __init__(self):
        super().__init__("Управление обработкой")

        self.analysis_toggle_button = QPushButton("Запустить анализ")
        self.pause_toggle_button = QPushButton("Пауза")
        self.capture_button = QPushButton("Зафиксировать кадр")
        self.capture_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.analysis_toggle_button)
        layout.addWidget(self.pause_toggle_button)
        layout.addWidget(self.capture_button)
        self.setLayout(layout)


class SettingsGroup(QGroupBox):
    def __init__(
        self,
        confidence_threshold: float = 0.4,
    ):
        super().__init__("Параметры точности")

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(1, 100)
        self.conf_slider.setValue(int(confidence_threshold * 100))
        self.conf_value_label = QLabel(f"{confidence_threshold:.2f}")

        conf_widget = QWidget()
        conf_layout = QHBoxLayout(conf_widget)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        conf_layout.setSpacing(8)
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_value_label)

        form = QFormLayout()
        form.addRow("Порог уверенности:", conf_widget)
        self.setLayout(form)


class ClassesGroup(QGroupBox):
    selection_changed = Signal(set)

    def __init__(self, class_names: list[str]):
        super().__init__("Отображаемые классы")

        self.class_checkboxes: dict[int, QCheckBox] = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(6)

        for class_id, class_name in enumerate(class_names):
            checkbox = QCheckBox(class_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._emit_current_selection)

            self.class_checkboxes[class_id] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        self.setLayout(layout)
        self.setMinimumHeight(270)

    def _emit_current_selection(self):
        self.selection_changed.emit(self.get_enabled_class_ids())

    def get_enabled_class_ids(self) -> set[int]:
        return {
            class_id
            for class_id, checkbox in self.class_checkboxes.items()
            if checkbox.isChecked()
        }

    def set_enabled_class_ids(self, class_ids: set[int]) -> None:
        for class_id, checkbox in self.class_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(class_id in class_ids)
            checkbox.blockSignals(False)


class StatusGroup(QGroupBox):
    def __init__(self):
        super().__init__("Статус системы")

        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedWidth(14)

        self.status_label = QLabel("Ожидание")
        self.detections_label = QLabel("0")

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        form = QFormLayout()
        form.addRow("Состояние:", status_widget)
        form.addRow("Детекций:", self.detections_label)
        self.setLayout(form)

    def update_metrics(
        self,
        detections_count: int,
    ) -> None:
        self.detections_label.setText(str(detections_count))

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.status_dot.setStyleSheet(f"color: {self._get_status_color(text)};")

    def _get_status_color(self, text: str) -> str:
        normalized = text.lower()

        if "ошибка" in normalized:
            return "#F85149"

        if normalized in ("идёт анализ", "обработка продолжена"):
            return "#3FB950"

        if normalized in ("ожидание", "готово", "видео выбрано"):
            return "#8F9AAA"

        if "пауза" in normalized or "приостанов" in normalized:
            return "#D29922"

        return "#8F9AAA"
