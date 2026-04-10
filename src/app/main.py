import sys
from PySide6.QtWidgets import QApplication

from app.config import theme
from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.STYLESHEET)
    theme.apply_application_font(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
