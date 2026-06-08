# This Python file uses the following encoding: utf-8
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap
import numpy as np
from PIL import Image, ImageOps
import cv_utils

class DocumentImage:
    MAX_CORNERS = 4

    A4_150DPI = (1240, 1754)
    @classmethod
    def from_path(cls, path):
        img = cv.imread(path, cv.IMREAD_GRAYSCALE)
        img = cv_utils.binary_threshold(img)
        if img is None:
            return None
        return cls(img)

    def __init__(self, image_arr):
        self._image_arr = image_arr
        self.corners = []

    def content(self):
        return self._image_arr

    def is_grayscale(self):
        return self._image_arr.ndim == 2

    def is_rgb(self):
        return self._image_arr.ndim == 3 and self._image_arr.shape[2] == 3

    def correct_perspective(self):
        if not self.corners:
            return self._image_arr

        page_corners = self.order_corners()
        top_left, top_right, bottom_right, bottom_left = page_corners

        width_top    = np.linalg.norm(top_right - top_left)
        width_bottom = np.linalg.norm(bottom_right - bottom_left)
        W = int(max(width_top, width_bottom))

        height_left  = np.linalg.norm(bottom_left - top_left)
        height_right = np.linalg.norm(bottom_right - top_right)
        H = int(max(height_left, height_right))

        perfect_square = np.array([
            [0,     0    ],
            [W - 1, 0    ],
            [W - 1, H - 1],
            [0,     H - 1],
        ], dtype=np.float32)

        M, _ = cv.findHomography(page_corners, perfect_square)
        warped = cv.warpPerspective(self._image_arr, M, (W, H))

        return warped

    def order_corners(self):
        if not self.corners:
            return []

        pts = np.array([[p.x(), p.y()] for p in self.corners], dtype=np.float32)
        pts = pts.reshape(4, 2).astype(np.float32)
        ordered = np.zeros((4, 2), dtype=np.float32)

        s = pts.sum(axis=1)

        # top-left
        ordered[0] = pts[np.argmin(s)]
        # bottom-right
        ordered[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        # top-right
        ordered[1] = pts[np.argmin(diff)]
        # bottom-left
        ordered[3] = pts[np.argmax(diff)]

        return ordered


    def pil_image(self):
        arr = self.correct_perspective()

        if arr.dtype != np.uint8:
            arr = (arr * 255).clip(0, 255).astype(np.uint8)

        if self.is_grayscale():
            pil_image = Image.fromarray(arr).convert("RGB")
        elif self.is_rgb() or arr.shape[2] == 4:
           pil_image = Image.fromarray(cv.cvtColor(arr, cv.COLOR_BGR2RGB))
           if pil_image.mode != "RGB":
               pil_image = pil_image.convert("RGB")
        else:
            raise ValueError(f"Unsupported image shape: {arr.shape}")

        return ImageOps.pad(pil_image, self.A4_150DPI, color=(255, 255, 255), method=Image.LANCZOS)

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
        if self.is_grayscale():
            qimage = self._grayscale_pixmap()
        elif self.is_rgb():
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