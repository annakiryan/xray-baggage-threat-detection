import sys

from PySide6.QtWidgets import QApplication

from app.config.config_service import ConfigService
from app.config.model_config_service import ModelConfigService
from app.ui.main_window import MainWindow
from app.logging import LoggerService
from app.session import AnalysisSession

LoggerService.configure(logs_dir="logs")


APP_CONFIG_PATH = "configs/app_config.json"
MODEL_CONFIG_PATH = "models/xray_yolo11n/config.json"


def main():
    app_config = ConfigService.load_app_config(APP_CONFIG_PATH)
    model_config = ModelConfigService.load_model_config(MODEL_CONFIG_PATH)

    app = QApplication(sys.argv)

    session = AnalysisSession(
        model_config=model_config,
        device=app_config.device,
        confidence_threshold=app_config.default_confidence_threshold,
        iou_threshold=app_config.default_iou_threshold,
        frame_skip=app_config.default_frame_skip,
        draw_enabled=True,
        logs_dir=app_config.logs_dir,
        results_dir=app_config.results_dir,
        default_video=app_config.default_video,
    )

    window = MainWindow(session)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
