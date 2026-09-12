#!/usr/bin/env python3
"""
Take a label image (already cropped to the label region, or a full page
where the label fills it) and produce a print-ready PDF that is exactly
4in x 6in, with the label content scaled up to fill as much of that page
as possible without distorting the barcode.

Why autocrop + fit-to-canvas, rather than just resizing the whole page:
Vinted's PDFs are typically laid out on an 8.5x11 (or A4) page with a lot
of white margin around the actual label artwork. Naively resizing that
full page down to 4x6 shrinks the real label content along with the
margins, wasting most of the label and producing a small, low-density
barcode. Cropping to the true content bounding box first, then scaling
that up to fill 4x6, is what makes the barcode big and scannable.

Usage:
    python fit_label_4x6.py input.png output.pdf [--dpi 400] [--threshold 245] [--no-crop]

--no-crop: skip the whitespace autocrop step (use when the input image has
already been manually cropped to exactly the label, e.g. by you visually
inspecting a rendered page and cropping it with PIL yourself).
"""
import argparse
import io

import numpy as np
from PIL import Image
import img2pdf


def autocrop(img: Image.Image, threshold: int = 245, pad_px: int = 6) -> Image.Image:
    """Crop to the bounding box of non-white content."""
    gray = img.convert("L")
    arr = np.array(gray)
    mask = arr < threshold
    if not mask.any():
        return img  # blank image, nothing to crop
    ys, xs = np.where(mask)
    top = max(0, int(ys.min()) - pad_px)
    left = max(0, int(xs.min()) - pad_px)
    bottom = min(arr.shape[0] - 1, int(ys.max()) + pad_px)
    right = min(arr.shape[1] - 1, int(xs.max()) + pad_px)
    return img.crop((left, top, right + 1, bottom + 1))


def fit_to_canvas(img: Image.Image, canvas_w_px: int, canvas_h_px: int) -> Image.Image:
    """Scale img to fill as much of the canvas as possible (preserving aspect
    ratio, no distortion), then center it on a white canvas of exact size."""
    img_w, img_h = img.size
    scale = min(canvas_w_px / img_w, canvas_h_px / img_h)
    new_w = max(1, round(img_w * scale))
    new_h = max(1, round(img_h * scale))
    # LANCZOS for upscaling keeps edges (barcode bars) as sharp as possible
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (canvas_w_px, canvas_h_px), "white")
    x = (canvas_w_px - new_w) // 2
    y = (canvas_h_px - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to the label image (PNG/JPG) to fit onto 4x6")
    ap.add_argument("output", help="Path to write the resulting 4x6in PDF")
    ap.add_argument("--dpi", type=int, default=400,
                     help="Effective print resolution of the output canvas.")
    ap.add_argument("--threshold", type=int, default=245,
                     help="Grayscale value (0-255) below which a pixel counts as content, not background.")
    ap.add_argument("--no-crop", action="store_true",
                     help="Skip autocrop; just fit/pad the image as-is.")
    args = ap.parse_args()

    img = Image.open(args.input)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if img.mode == "L":
        img = img.convert("RGB")

    if not args.no_crop:
        img = autocrop(img, threshold=args.threshold)

    canvas_w_px = round(4 * args.dpi)
    canvas_h_px = round(6 * args.dpi)
    final = fit_to_canvas(img, canvas_w_px, canvas_h_px)

    buf = io.BytesIO()
    final.save(buf, format="PNG")
    pdf_bytes = img2pdf.convert(
        buf.getvalue(),
        layout_fun=img2pdf.get_layout_fun((img2pdf.in_to_pt(4), img2pdf.in_to_pt(6))),
    )
    with open(args.output, "wb") as f:
        f.write(pdf_bytes)

    print(f"Wrote {args.output}: {canvas_w_px}x{canvas_h_px}px canvas @ {args.dpi} DPI, exactly 4in x 6in page.")


if __name__ == "__main__":
    main()
