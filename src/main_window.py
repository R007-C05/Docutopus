# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QMainWindow, QFileDialog, QPushButton
import qtawesome as qta
from ui_main_window import Ui_MainWindow
import cv_utils

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Docutopus")
        self.showMaximized()

        self.selectionModeButtons = [self.ui.saveSelectionButton, self.ui.clearSelectionButton, self.ui.cancelSelectionButton]
        self.toggle_selection_buttons(self.ui.imageView.selectionMode)

        self.ui.saveSelectionButton.setIcon(qta.icon("mdi.check"))
        self.ui.clearSelectionButton.setIcon(qta.icon("fa5.square"))
        self.ui.selectectionModeButton.setIcon(qta.icon("ei.file-edit"))

        self.ui.actionScanImage.triggered.connect(self.open_file)

        self.ui.rotateLButton.clicked.connect(lambda: self.ui.imageView.rotate_image(-1))
        self.ui.rotateRButton.clicked.connect(lambda: self.ui.imageView.rotate_image(+1))
        self.ui.fitToWindowButton.clicked.connect(self.ui.imageView.fit_to_window)

        self.ui.selectectionModeButton.clicked.connect(self.toggle_selection_mode)
        self.ui.cancelSelectionButton.clicked.connect(self.toggle_selection_mode)
        self.ui.saveSelectionButton.clicked.connect(self.save_selection)
        self.ui.clearSelectionButton.clicked.connect(self.ui.imageView.clear_selection)

    def toggle_selection_buttons(self, selection_mode):
        if selection_mode:
            self.ui.selectectionModeButton.hide()
            for btn in self.selectionModeButtons:
                btn.show()
            return

        self.ui.selectectionModeButton.show()
        for btn in self.selectionModeButtons:
            btn.hide()

    def toggle_selection_mode(self):
        self.ui.imageView.toggle_selection_mode()
        self.toggle_selection_buttons(self.ui.imageView.selectionMode)

    def save_selection(self):
        self.ui.imageView.save_selection()
        self.toggle_selection_buttons(self.ui.imageView.selectionMode)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scan Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if path:
            self.ui.imageView.load_image_from_file(path)

