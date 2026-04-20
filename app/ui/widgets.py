from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class SourceGroup(QGroupBox):
    def __init__(self):
        super().__init__("Источник данных")

        self.open_video_button = QPushButton("Открыть видео")

        form = QFormLayout()
        form.addRow(self.open_video_button)
        self.setLayout(form)


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

        self.status_label = QLabel("Ожидание")
        self.detections_label = QLabel("0")

        form = QFormLayout()
        form.addRow("Состояние:", self.status_label)
        form.addRow("Детекций:", self.detections_label)
        self.setLayout(form)

    def update_metrics(
        self,
        detections_count: int,
    ) -> None:
        self.detections_label.setText(str(detections_count))

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
