import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Receipt Review Software")
        self.setGeometry(100, 100, 1200, 800)
        
        label = QLabel("PySide6 セットアップ完了！", self)
        label.setStyleSheet("font-size: 24px;")
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
