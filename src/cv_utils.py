# This Python file uses the following encoding: utf-8
import cv2 as cv

def binary_threshold(img):
    blur = cv.GaussianBlur(img, (5,5), 0)
    ret, th = cv.threshold(blur, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    return th

def export_to_pdf(image_list, filename="output.pdf"):
    pages = []
    for img in image_list:
        pil_image = img.pil_image()
        pil_image.encoderinfo = {}
        pil_image.format = "PNG"
        pages.append(pil_image)

    if not pages:
        return
    if len(pages) == 1:
        pages[0].save(filename, format="PDF")
    else:
        pages[0].save(filename, format="PDF", save_all=True, append_images=pages[1:])