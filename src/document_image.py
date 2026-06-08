# This Python file uses the following encoding: utf-8
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap
import numpy as np
from PIL import Image, ImageOps

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
        self.corners = []

    def content(self):
        return self._image_arr

    def is_grayscale(self):
        return self._image_arr.ndim == 2

    def is_rgb(self):
        return self._image_arr.ndim == 3 and self._image_arr.shape[2] == 3


    def crop(self):
        # TODO: Need to convert zoomed in points to real coordinates
        if not self.corners:
            # Make the image corners the corners
            return self._image_arr

        pts_src = np.array([[p.x(), p.y()] for p in self.corners], dtype=np.float32)

        # Compute output width and height
        width_top = np.linalg.norm(pts_src[0] - pts_src[1])
        width_bottom = np.linalg.norm(pts_src[3] - pts_src[2])
        width = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(pts_src[0] - pts_src[3])
        height_right = np.linalg.norm(pts_src[1] - pts_src[2])
        height = int(max(height_left, height_right))

        pts_dst = np.array([
            [0, 0],
            [width-1, 0],
            [width-1, height-1],
            [0, height-1]
        ], dtype=np.float32)

        # Perspective transform
        M = cv.getPerspectiveTransform(pts_src, pts_dst)
        cropped = cv.warpPerspective(self._image_arr, M, (width, height))

        return cropped


    def pil_image(self):
        arr = self.crop()

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