#!/usr/bin/env python3
"""
Render each page of a PDF to a high-resolution PNG.

Use this first, on the original Vinted-generated PDF, so you can *look at*
each page and decide what's actually the shipping label versus a packing
slip, return instructions, or other filler content. Vinted labels vary in
layout (single-page label-only PDFs, or a label plus extra pages/sections),
so visual inspection before cropping is the reliable way to find the right
boundaries -- don't assume a fixed layout.

Usage:
    python render_pages.py input.pdf /path/to/output_prefix [--dpi 400]

Produces output_prefix_page1.png, output_prefix_page2.png, etc.
"""
import argparse
import pypdfium2 as pdfium


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output_prefix")
    ap.add_argument("--dpi", type=int, default=400,
                     help="Rendering resolution. 400+ recommended so barcodes stay crisp.")
    args = ap.parse_args()

    pdf = pdfium.PdfDocument(args.input)
    scale = args.dpi / 72  # pypdfium2 renders at 72 DPI base

    for i, page in enumerate(pdf):
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        out_path = f"{args.output_prefix}_page{i + 1}.png"
        pil_image.save(out_path)
        print(f"Saved {out_path} ({pil_image.size[0]}x{pil_image.size[1]}px @ {args.dpi} DPI)")


if __name__ == "__main__":
    main()
