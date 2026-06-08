# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
import qtawesome as qta
from document_image_list import DocumentImageList
from document_image import DocumentImage
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

        self.ui.actionFrom_image.triggered.connect(self.open_new_image)
        self.ui.actionFrom_folder.triggered.connect(self.open_new_directory)

        self.image_list = DocumentImageList()

        # Image transformations
        self.ui.rotateLButton.clicked.connect(lambda: self.ui.imageView.rotate_image(-1))
        self.ui.rotateRButton.clicked.connect(lambda: self.ui.imageView.rotate_image(+1))

        self.ui.fitToWindowButton.clicked.connect(self.ui.imageView.fit_to_window)

        # Selection
        self.ui.selectectionModeButton.clicked.connect(self.toggle_selection_mode)
        self.ui.cancelSelectionButton.clicked.connect(self.toggle_selection_mode)
        self.ui.saveSelectionButton.clicked.connect(self.save_selection)
        self.ui.clearSelectionButton.clicked.connect(self.ui.imageView.clear_selection)

        # Add / Remove page
        self.ui.addImageButton.clicked.connect(self.add_image)
        self.ui.removeImageButton.clicked.connect(self.remove_image)

        # Page navigation
        self.ui.nextPageButton.clicked.connect(self.next_page)
        self.ui.previousPageButton.clicked.connect(self.previous_page)

        # Page ordering
        self.ui.moveLeftButton.clicked.connect(self.move_page_left)
        self.ui.moveRightButton.clicked.connect(self.move_page_right)

        self.ui.saveButton.clicked.connect(self.export_pdf)

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

    def open_new_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scan Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if path:
            doc_image = DocumentImage.from_path(path)
            if doc_image:
                self.image_list.clear()
                self.image_list.append(doc_image)
                self.ui.imageView.load_new_image(doc_image)
                return
            QMessageBox.critical(self, "Error", "Failed to load image.")

    def open_new_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Open Directory", "")
        if path:
            images = cv_utils.open_images_in_path(path)
            if images:
                self.image_list.clear()
                doc_image = None
                for image in images:
                    doc_image = DocumentImage.from_path(image)
                    if doc_image:
                        self.image_list.append(doc_image)
                if doc_image:
                    self.ui.imageView.load_new_image(doc_image)
                    return
                QMessageBox.critical(self, "Error", "Failed to load image.")
            QMessageBox.critical(self, "Error", "Failed to load folder.")

    def add_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scan Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if path:
            doc_image = DocumentImage.from_path(path)
            if doc_image:
                self.image_list.append(doc_image)
                self.ui.imageView.load_new_image(doc_image)
                return
            QMessageBox.critical(self, "Error", "Failed to load image.")

    def export_pdf(self):
        if self.image_list.empty():
            return
        if self.ui.imageView.current_image:
            self.ui.imageView.fit_to_window()
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if path:
            if not path.endswith(".pdf"):
                path += ".pdf"
            cv_utils.export_to_pdf(self.image_list, path)

    def remove_image(self):
        if self.ui.imageView.selectionMode:
            self.toggle_selection_mode()

        doc_image = self.image_list.remove()
        if doc_image is None:
            self.ui.imageView.clear_image()
        else:
            self.ui.imageView.load_new_image(doc_image)

    def next_page(self):
        image = self.image_list.next()
        if image:
            self.ui.imageView.load_new_image(image)

    def previous_page(self):
        image = self.image_list.previous()
        if image:
            self.ui.imageView.load_new_image(image)

    def move_page_left(self):
        self.image_list.move_up()

    def move_page_right(self):
        self.image_list.move_down()