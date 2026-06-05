# This Python file uses the following encoding: utf-8
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap
import numpy as np

def binary_threshold(img):
    blur = cv.GaussianBlur(img, (5,5), 0)
    ret, th = cv.threshold(blur, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    return th

def pixmap_to_cv(pixmap):
    image = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)

    width = image.width()
    height = image.height()

    ptr = image.bits()
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))

    return cv.cvtColor(arr, cv.COLOR_RGBA2BGR)

def cv_to_pixmap(cv_img):
    rgb = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)

    h, w, ch = rgb.shape
    bytes_per_line = ch * w

    image = QImage(
        rgb.data,
        w,
        h,
        bytes_per_line,
        QImage.Format_RGB888
    )

    return QPixmap.fromImage(image.copy())