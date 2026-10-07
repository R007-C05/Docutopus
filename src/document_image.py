# This Python file uses the following encoding: utf-8
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap
import numpy as np
from PIL import Image, ImageOps
from enum import Enum

class ScanMode(Enum):
    OCR = 0
    Document = 1

class Point:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y


class DocumentImage:
    MAX_CORNERS = 4
    A4_150DPI = (1240, 1754)

    @classmethod
    def from_path(cls, path):
        img = cv.imread(path, cv.IMREAD_COLOR)
        if img is None:
            return None
        return cls(img)

    def __init__(self, image_arr):
        self._image_arr = image_arr
        self.scan_mode = ScanMode.Document
        self.corners = []
        self.text_selections = []

    def set_mode(self, scan_mode: ScanMode):
        self.scan_mode = scan_mode

    def set_corners(self, corner_list):
        for x, y in corner_list:
            self.corners.append(Point(x.item(), y.item()))

    def get_text_images(self):
        return [
            self._warp_quad(self._image_arr, self._order_points(selection))
            for selection in self.text_selections
            if len(selection) == self.MAX_CORNERS
        ]

    def content(self):
        return self._image_arr

    def is_grayscale(self):
        return self._image_arr.ndim == 2

    def is_rgb(self):
        return self._image_arr.ndim == 3 and self._image_arr.shape[2] == 3

    def correct_perspective(self):
        if not self.corners:
            return self._image_arr
        return self._warp_quad(self._image_arr, self.order_corners())


    @staticmethod
    def _order_points(points):
        pts = np.array([[p.x, p.y] for p in points], dtype=np.float32).reshape(4, 2)
        ordered = np.zeros((4, 2), dtype=np.float32)

        s = pts.sum(axis=1)
        ordered[0] = pts[np.argmin(s)]      # top-left
        ordered[2] = pts[np.argmax(s)]      # bottom-right

        diff = np.diff(pts, axis=1)
        ordered[1] = pts[np.argmin(diff)]   # top-right
        ordered[3] = pts[np.argmax(diff)]   # bottom-left

        return ordered

    @staticmethod
    def _warp_quad(image, page_corners):
        top_left, top_right, bottom_right, bottom_left = page_corners

        W = int(max(np.linalg.norm(top_right - top_left),
                    np.linalg.norm(bottom_right - bottom_left)))
        H = int(max(np.linalg.norm(bottom_left - top_left),
                    np.linalg.norm(bottom_right - top_right)))
        W, H = max(W, 1), max(H, 1)

        target = np.array([
            [0,     0    ],
            [W - 1, 0    ],
            [W - 1, H - 1],
            [0,     H - 1],
        ], dtype=np.float32)

        M, _ = cv.findHomography(page_corners, target)
        return cv.warpPerspective(image, M, (W, H))

    def order_corners(self):
        if not self.corners:
            return []
        return self._order_points(self.corners)

    def binary_threshold(self, img, value):
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(img, (value, value), 0)
        th = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 21, 5)
        return th

    def pil_image(self):
        arr = self.correct_perspective()
        arr = self.binary_threshold(arr, 5)
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