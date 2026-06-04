# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QMainWindow, QFileDialog
from PySide6.QtGui import QTransform
from ui_main_window import Ui_MainWindow
import cv_utils

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Docutopus")
        self.showMaximized()

        self.ui.actionScanImage.triggered.connect(self.open_file)

        self.ui.rotateLButton.clicked.connect(lambda: self.rotate_image(-1))
        self.ui.rotateRButton.clicked.connect(lambda: self.rotate_image(+1))
        self.ui.fitToWindowButton.clicked.connect(self.ui.imageView.fit_to_window)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scan Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if path:
            self.ui.imageView.load_image_from_file(path)

    def rotate_image(self, direction):
        if self.ui.imageView.current_image is None:
            return
        transform = QTransform().rotate(direction*90)
        rotated = self.ui.imageView.current_image.transformed(transform)
        self.ui.imageView.reload_image(rotated)
