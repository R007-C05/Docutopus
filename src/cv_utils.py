# This Python file uses the following encoding: utf-8
import cv2 as cv
import numpy as np

def open_image(path):
    img = cv.imread(path, cv.IMREAD_GRAYSCALE)
    img = cv.resize(img, None, fx=0.5, fy=0.5, interpolation=cv.INTER_AREA)
    blur = cv.GaussianBlur(img, (5,5), 0)
    ret, th = cv.threshold(blur, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    if img is not None:
        cv.imwrite("output.jpg", img)