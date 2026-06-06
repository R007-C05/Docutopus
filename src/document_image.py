# This Python file uses the following encoding: utf-8
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap

class DocumentImage:
    MAX_CORNERS = 4

    @classmethod
    def from_path(cls, path):
        img = cv.imread(path, cv.IMREAD_COLOR)
        if img is None:
            return None
        return cls(img)

    def __init__(self, image_arr):
        self._image_arr = image_arr
        self.corners = []

    def width(self):
        return self._image_arr.shape[1]

    def height(self):
        return self._image_arr.shape[0]

    def rotate(self, direction):
        if direction > 0:
            self._image_arr = cv.rotate(self._image_arr, cv.ROTATE_90_CLOCKWISE)
        else:
            self._image_arr = cv.rotate(self._image_arr, cv.ROTATE_90_COUNTERCLOCKWISE)

    def pixmap(self):
        if self._image_arr.ndim == 2:
            qimage = self._grayscale_pixmap()
        elif self._image_arr.ndim == 3 and self._image_arr.shape[2] == 3:
            qimage = self._rgb_pixmap()
        else:
            raise ValueError(f"Unsupported image shape: {self._image_arr.shape}")

        return QPixmap.fromImage(qimage.copy())

    def _grayscale_pixmap(self):
        h, w = self._image_arr.shape
        bytes_per_line = w
        return QImage(self._image_arr.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)

    def _rgb_pixmap(self):
        rgb = cv.cvtColor(self._image_arr, cv.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        return QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)