# This Python file uses the following encoding: utf-8
import cv2 as cv
from pathlib import Path
from PIL.ExifTags import TAGS
import datetime
import onnxruntime as ort
import numpy as np
from document_image import ScanMode
from PIL import Image, ImageOps
import pytesseract
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

OCR_MODEL_ENGLISH = "microsoft/trocr-base-handwritten"
OCR_MODEL_SPANISH = "ifesther/trocr-spanish-handwritten"
TR_OCR_MODEL = OCR_MODEL_SPANISH
processor = TrOCRProcessor.from_pretrained(TR_OCR_MODEL)
tr_ocr_model = VisionEncoderDecoderModel.from_pretrained(TR_OCR_MODEL).eval()

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

reader = easyocr.Reader(["es", "en"])
session = ort.InferenceSession(
    "docNet.onnx",
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name


def export_as_image(img):
    pil_image = img.pil_image()
    pil_image.encoderinfo = {}
    pil_image.format = "PNG"
    return pil_image


def tr_ocr_line(pil_image):
    pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values
    with torch.no_grad():
        ids = tr_ocr_model.generate(pixel_values, max_new_tokens=64)
    return processor.batch_decode(ids, skip_special_tokens=True)[0]

def as_pil(arr):
    if arr.dtype != np.uint8:
        arr = (arr * 255).clip(0, 255).astype(np.uint8)

    if arr.ndim == 2:
        pil_image = Image.fromarray(arr).convert("RGB")
    elif (arr.ndim == 3 and arr.shape[2] == 3) or arr.shape[2] == 4:
       pil_image = Image.fromarray(cv.cvtColor(arr, cv.COLOR_BGR2RGB))
       if pil_image.mode != "RGB":
           pil_image = pil_image.convert("RGB")
    else:
        raise ValueError(f"Unsupported image shape: {arr.shape}")

    return ImageOps.pad(pil_image, (1240, 1754), color=(255, 255, 255), method=Image.LANCZOS)



def image_to_text(text_img):
    #return pytesseract.image_to_string(text_img, lang="spa")
    return tr_ocr_line(as_pil(text_img))

def export_as_text(img):
    result = []
    for text_img in img.get_text_images():
        #text_img = cv.resize(text_img, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC)
        text = image_to_text(text_img)
        print(text)
        result.append(as_pil(text_img))
    return result

def export_to_pdf(image_list, filename="output.pdf"):
    pages = []
    for img in image_list:
        if img.scan_mode == ScanMode.Document:
            document_page = export_as_image(img)
            pages.append(document_page)
        else:
            for text_page in export_as_text(img):
                pages.append(text_page)

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

def find_corners_DocCoordNet(image, scale_factor=1):
    h, w = image.shape[:2]
    input_size = 224

    resized = cv.resize(image, (input_size, input_size))
    resized = cv.cvtColor(resized, cv.COLOR_BGR2RGB)

    x = resized.astype(np.float32) / 255.0
    x = np.expand_dims(x, axis=0)

    outputs = session.run(None, {input_name: x})

    coords = outputs[0][0]
    corners = coords[:8].reshape(4, 2)

    corners[:, 0] *= w/scale_factor
    corners[:, 1] *= h/scale_factor

    return corners.astype(float)


def preprocess_document_image(image):
    if image is None:
        raise ValueError("Image is None — check that it loaded correctly.")
    max_dim = 320

    scale = min(1.0, max_dim / max(image.shape[:2]))
    if scale < 1:
        scaled_image = cv.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv.INTER_AREA
        )
    if scaled_image.dtype != np.uint8:
        scaled_image = scaled_image.astype(np.uint8)

    if len(scaled_image.shape) == 2:
        scaled_image = cv.cvtColor(scaled_image, cv.COLOR_GRAY2BGR)

    kernel = np.ones((5, 5), np.uint8)
    smoothed = cv.morphologyEx(scaled_image, cv.MORPH_CLOSE, kernel, iterations=3)

    h, w = scaled_image.shape[:2]

    if w <= 40 or h <= 40:
        raise ValueError(f"Image is too small for GrabCut: {w}x{h}")

    mask = np.zeros((h, w), np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    rect = (20, 20, w - 40, h - 40)
    cv.grabCut(smoothed, mask, rect, bgdModel, fgdModel, 5, cv.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)
    cutout = smoothed * mask2[:, :, np.newaxis]
    gray = cv.cvtColor(cutout, cv.COLOR_BGR2GRAY)
    return gray, scale

def order_points(pts):
    rect = np.zeros((4, 2), dtype='float32')
    pts = np.array(pts)
    s = pts.sum(axis=1)
        # Top-left point will have the smallest sum.
    rect[0] = pts[np.argmin(s)]
        # Bottom-right point will have the largest sum.
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
        # Top-right point will have the smallest difference.
    rect[1] = pts[np.argmin(diff)]
        # Bottom-left will have the largest difference.
    rect[3] = pts[np.argmax(diff)]
        # Return the ordered coordinates.
    return rect.astype('float')

def test(image):
    img, scale = preprocess_document_image(image)
    scaled_image = cv.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv.INTER_AREA
    )
    con = np.zeros_like(scaled_image)
    canny = cv.Canny(img, 0, 200)
    #canny = cv.dilate(canny, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
    contours, hierarchy = cv.findContours(canny, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
    page = sorted(contours, key=cv.contourArea, reverse=True)[:5]
    con = cv.drawContours(con, page, -1, (0, 255, 255), 3)
    return con


def find_corners_traditional(image):
    img, scale = preprocess_document_image(image)
    canny = cv.Canny(img, 0, 200)
    canny = cv.dilate(canny, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))

    contours, _ = cv.findContours(canny, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
    page = sorted(contours, key=cv.contourArea, reverse=True)[:5]

    corners = None
    for c in page:
        epsilon = 0.02 * cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, epsilon, True)
        if len(approx) == 4:
            corners = approx
            break

    if corners is None:
        h, w = image.shape[:2]
        return np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=float)

    return corners.reshape(4, 2).astype(float) / scale

def find_corners_mixed(image):
    img, scale = preprocess_document_image(image)
    return find_corners_DocCoordNet(img, scale)