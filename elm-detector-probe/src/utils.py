"""
Lightweight utilities for image handling.

Exposes:
- read_image_b64(path): Return a base64 data-URL string for VLM input.
"""

from __future__ import annotations

import os, base64
from PIL import Image, ImageFilter

_MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def read_image_b64(path: str) -> str:
    """Read an image file and return a base64 data URL string.

    The format is: "data:<mime>;base64,<b64>".
    MIME type is inferred from the file extension and defaults to JPEG.
    """
    ext = os.path.splitext(path)[1].lower()
    mime = _MIME_BY_EXT.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def save_b64_jpg(b64_data, out_path):
    if b64_data.startswith("data:"):
        b64_data = b64_data.split(",",1)[1]
    img_bytes = base64.b64decode(b64_data)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

def normalize_image(im: Image.Image, target_long=768):
    im = im.convert("RGB")
    w,h = im.size
    if max(w,h) != target_long:
        if w >= h:
            new_w = target_long
            new_h = int(h * target_long / w)
        else:
            new_h = target_long
            new_w = int(w * target_long / h)
        im = im.resize((new_w, new_h), Image.LANCZOS)
    return im

def perturb_light(im: Image.Image):
    w,h = im.size
    scale = 640/max(w,h)
    if scale < 1.0:
        im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(radius=0.5))
    return im

def save_jpeg_strip_exif(im: Image.Image, out_path, quality=80):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, format="JPEG", quality=quality, optimize=True)



__all__ = ["read_image_b64"]

