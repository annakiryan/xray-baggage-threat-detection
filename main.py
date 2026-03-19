import sys

from PySide6.QtWidgets import QApplication

from app.services.config_service import ConfigService
from app.core.model_config import ModelConfigService
from app.ui.main_window import MainWindow


APP_CONFIG_PATH = "configs/app_config.json"
MODEL_CONFIG_PATH = "models/xray_yolo_nano_1/config.json"


def main():
    app_config = ConfigService.load_app_config(APP_CONFIG_PATH)
    model_config = ModelConfigService.load_model_config(MODEL_CONFIG_PATH)

    app = QApplication(sys.argv)

    window = MainWindow(
        model_config=model_config,
        device=app_config.device,
        confidence_threshold=app_config.default_confidence_threshold,
        iou_threshold=app_config.default_iou_threshold,
        frame_skip=app_config.default_frame_skip,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
