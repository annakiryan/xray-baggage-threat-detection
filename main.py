import sys
import os
import ctypes
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.app_factory import create_main_window

os.environ["QT_LOGGING_RULES"] = "*.warning=false"
APP_ICON_PATH = Path("assets/icons/app_icon.ico")
APP_ID = "xray.baggage.threat.detection"


def main() -> int:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

    app = QApplication(sys.argv)

    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))

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
