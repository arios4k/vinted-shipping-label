# vinted-shipping-label

A [Claude Skill](https://www.anthropic.com/news/skills) that converts a Vinted-generated USPS or FedEx shipping label PDF into a print-ready **4×6 in (100×150 mm)** PDF sized for thermal label printers (e.g. ORGSTA, Rollo, MUNBYN).

Vinted's exported PDFs are usually a full US-Letter/A4 page with the label stuck in one corner, sometimes bundled with a packing slip or return-policy page. This skill:

- Renders the PDF pages to images so it can *see* the layout before touching it (layouts aren't consistent, so a fixed crop isn't reliable)
- Identifies the actual label region — barcode(s), tracking number, addresses, postage/service class — and discards packing slips, receipts, and instructions
- Autocrops whitespace and scales the label up to fill a true 4×6 in canvas, without distorting the barcode
- Re-renders the output and checks it before handing it back

## What's in this repo

```
vinted-shipping-label/
├── SKILL.md                  # The skill definition Claude reads
└── scripts/
    ├── render_pages.py       # Renders PDF pages to high-DPI PNGs for inspection
    └── fit_label_4x6.py      # Autocrops + scales a label image onto an exact 4x6in PDF canvas
```

## Requirements

The scripts need:

- Python 3.9+
- [`pypdfium2`](https://pypi.org/project/pypdfium2/)
- [`Pillow`](https://pypi.org/project/Pillow/)
- [`numpy`](https://pypi.org/project/numpy/)
- [`img2pdf`](https://pypi.org/project/img2pdf/)

Install them with:

```bash
pip install pypdfium2 Pillow numpy img2pdf
```

## Installing this skill

This is built for [Claude Skills](https://www.anthropic.com/news/skills) — reusable instruction sets Claude reads before doing a task.

1. Download or clone this repo.
2. Copy the `vinted-shipping-label/` folder into your Claude skills directory (the exact location depends on your setup — e.g. a `skills/` folder in Claude Code, or wherever your Claude product loads custom skills from).
3. Make sure the Python dependencies above are available in the environment Claude runs code in.

Once installed, just tell Claude something like:

> Here's my Vinted shipping label PDF, can you make it print on my thermal label printer?

Claude will pick up the skill automatically from the filename/context — no need to invoke it by name.

## Usage (manual / outside Claude)

You can also run the two scripts by hand:

```bash
# 1. Render the original PDF so you can inspect each page
python scripts/render_pages.py input.pdf /tmp/label_render --dpi 400

# 2. Look at /tmp/label_render_page1.png (etc.) and find the label region

# 3a. If the label fills its own page cleanly:
python scripts/fit_label_4x6.py /tmp/label_render_page1.png output.pdf --dpi 400

# 3b. If you need to crop out a specific region first, crop it manually with
#     PIL/any image tool, then run with --no-crop:
python scripts/fit_label_4x6.py /tmp/label_only.png output.pdf --dpi 400 --no-crop
```

Print the resulting PDF at **100% / "Actual size"** — not "fit to page" — or the printer will rescale it and throw off the barcode density.

## How it works

See [`SKILL.md`](./vinted-shipping-label/SKILL.md) for the full workflow and the reasoning behind each step (why visual inspection matters, why autocrop-then-scale beats a naive resize, and how output is validated before being handed off).

## License

[MIT](./LICENSE)

## Contributing

Issues and PRs welcome — especially reports of Vinted label layouts this doesn't handle well.
