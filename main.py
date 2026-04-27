import sys
import os

from PySide6.QtWidgets import QApplication, QMessageBox

from app.app_factory import create_main_window

os.environ["QT_LOGGING_RULES"] = "*.warning=false"


def main() -> int:
    app = QApplication(sys.argv)

    try:
        window = create_main_window()
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
