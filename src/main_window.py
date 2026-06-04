# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QMainWindow, QFileDialog
from ui_main_window import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Docutopus")

        self.ui.actionScanImage.triggered.connect(self.open_file)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scan Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if path:
            print(f"Image file is: {path}")

