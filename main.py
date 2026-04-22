import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config.config_service import ConfigService
from app.config.model_config_service import ModelConfigService
from app.session.analysis_session import AnalysisSession
from app.ui.analysis.analysis_page import AnalysisPage
from app.ui.history.history_page import HistoryPage
from app.ui.main_window.main_window import MainWindow


def build_app() -> MainWindow:
    config_path = Path("configs/app_config.json")
    app_config = ConfigService.load_app_config(config_path)

    model_config_path = Path(app_config.models_dir) / "xray_yolo10n/config.json"
    model_config = ModelConfigService.load_model_config(model_config_path)

    analysis_session = AnalysisSession(
        default_video=app_config.default_video,
        logs_dir=app_config.logs_dir,
        results_dir=app_config.results_dir,
        model_config=model_config,
        device=app_config.device,
        confidence_threshold=app_config.default_confidence_threshold,
        iou_threshold=app_config.default_iou_threshold,
        frame_skip=app_config.default_frame_skip,
        draw_enabled=True,
    )

    analysis_page = AnalysisPage(session=analysis_session)
    history_page = HistoryPage(results_dir=app_config.results_dir)

    main_window = MainWindow(
        analysis_page=analysis_page,
        history_page=history_page,
        session=analysis_session,
    )

    return main_window


def main() -> int:
    app = QApplication(sys.argv)

    try:
        window = build_app()
        window.showMaximized()
        return app.exec()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Ошибка запуска приложения",
            str(e),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())