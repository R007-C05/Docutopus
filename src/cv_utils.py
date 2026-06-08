# This Python file uses the following encoding: utf-8
import cv2 as cv
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import datetime

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

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


def get_capture_time(image):
    try:
        with Image.open(image) as img:
            exif = img.getexif()

            for tag_id, value in exif.items():
                if TAGS.get(tag_id) == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").timestamp()
    except Exception:
        print("Error")

    return image.stat().st_mtime

def open_images_in_path(path):
    images = [file for file in Path(path).iterdir() if file.suffix.lower() in IMAGE_EXTENSIONS]
    images.sort(key=lambda img: get_capture_time(img))
    return images
