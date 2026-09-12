---
name: vinted-shipping-label
description: Converts a Vinted-generated USPS or FedEx shipping label PDF into a print-ready 4x6 inch (100x150mm) PDF sized for thermal label printers such as ORGSTA. Strips out packing slips, receipts, and any other extraneous pages/content Vinted bundles into the export, keeping only the actual label (barcode, tracking number, addresses, postage/service info), and scales it to fill the 4x6 page without distorting the barcode. Trigger this whenever the user mentions a Vinted shipping label, printing a 4x6 or thermal label, an ORGSTA (or similar thermal) printer, or uploads a PDF that turns out to be a USPS/FedEx label exported from Vinted -- even if they just say "resize this label" or "make this print on my label printer" without naming Vinted explicitly.
---

# Vinted Shipping Label → 4x6 Thermal Label PDF

## Why this needs judgment, not just a fixed crop

Vinted's PDF export isn't perfectly consistent — sometimes it's a single page
with the label sitting in one corner of a full US Letter / A4 page (lots of
white margin), sometimes there's a packing slip, return policy blurb, or
order summary bundled in as a second page or as extra text below the label
on the same page. A fixed crop rectangle will eventually clip a barcode or
leave junk text in the output. So: **render pages to images and actually
look at them before cropping.** That visual check is what makes this
reliable across the different layouts Vinted produces.

## Workflow

### 1. Render the PDF at high resolution

```bash
python scripts/render_pages.py input.pdf /tmp/label_render --dpi 400
```

This produces `/tmp/label_render_page1.png`, `_page2.png`, etc. Use `view`
on each one. 400 DPI is high enough that barcode bars stay sharp all the
way through cropping and rescaling — don't drop below ~300 DPI or the
barcode may blur or become unscannable after resizing.

### 2. Identify the label

Look at the rendered page(s) and determine:

- **Carrier**: USPS or FedEx (visible from the header/logo text, tracking
  number format, or barcode style). This is mainly useful for naming the
  output file and sanity-checking that you've found the right content —
  it doesn't change the cropping approach.
- **Which page and region is the actual label.** The label is the block
  containing: barcode(s), tracking number, "from" and "to" addresses,
  postage/service class, and any carrier routing barcodes. Everything else
  — "thank you for your order", packing slips, item descriptions, return
  instructions, printing instructions, terms/legal text, order numbers not
  part of the shipping barcode — is not part of the label and should be
  left out.
- Most Vinted exports put the whole label on one page with the rest of
  that page blank, and any packing-slip content on a separate page. In
  that case the "page" IS the label region (see step 3a). Occasionally a
  page mixes label content with other text — in that case you need a
  manual sub-crop (step 3b).

### 3a. Simple case: label fills its own page cleanly

If the label's page has no other content sharing it (packing slip is a
separate page, or there's no packing slip at all), just run the fit script
directly on that page's rendered PNG — it will autocrop the whitespace and
scale the remaining content to fill a 4x6 page:

```bash
python scripts/fit_label_4x6.py /tmp/label_render_page1.png /mnt/user-data/outputs/label_4x6_<random>.pdf --dpi 400
```

### 3b. Mixed case: label shares a page with other content

If a page has both the label and non-label text/sections, crop the label's
bounding box out first (using coordinates you read off the rendered image
— `view` shows pixel coordinates, or open the PNG and inspect it), then
run the fit script with `--no-crop` since it's already precisely cropped:

```python
from PIL import Image
img = Image.open("/tmp/label_render_page1.png")
label_only = img.crop((left, top, right, bottom))  # pixel coords of just the label
label_only.save("/tmp/label_only.png")
```

```bash
python scripts/fit_label_4x6.py /tmp/label_only.png /mnt/user-data/outputs/label_4x6_<random>.pdf --dpi 400 --no-crop
```

Leave a little padding around the barcode/text when you pick the crop box
— cropping exactly to the pixel edge risks shaving off a barcode bar or a
digit.

### 4. Validate before presenting

Re-render the output PDF and look at it:

```bash
python scripts/render_pages.py /mnt/user-data/outputs/label_4x6_<random>.pdf /tmp/final_check --dpi 150
```

Check the image for:
- The full barcode is present, unclipped, and not visibly blurred or
  smeared (this is the part that actually breaks scanning, so look
  closely here — zoom into the barcode region if it's small in the
  preview).
- Tracking number, addresses, and service markings are all visible and
  readable.
- No leftover packing-slip/instruction text.
- The page itself is exactly 4in x 6in — you can confirm with:
  ```python
  import pypdfium2 as pdfium
  pdf = pdfium.PdfDocument("output.pdf")
  w_pt, h_pt = pdf[0].get_size()
  print(w_pt/72, h_pt/72)  # should print 4.0 6.0
  ```

If anything's off (barcode clipped, leftover junk text, wrong aspect),
adjust the crop box or threshold and redo step 3 rather than presenting a
flawed label — a shipping label that doesn't scan is worse than a slow
turnaround.

### 5. Output

- Save to `/mnt/user-data/outputs/` with a unique filename, e.g.
  `label_4x6_<carrier>_<random 6-char suffix>.pdf`, so repeated runs in the
  same conversation don't collide or overwrite each other.
- Use `present_files` to hand it to the user.
- Briefly tell the user the carrier detected and to print at **100% /
  "Actual size"** (not "fit to page") — thermal printers and PDF viewers
  will otherwise rescale a correctly-sized 4x6 page and throw off the
  barcode density.

## Notes on quality

- Never redraw, OCR-and-regenerate, or re-typeset the label — always work
  with the original rendered image content. The goal is repositioning and
  cropping, not recreating.
- Keep everything in the RGB/grayscale image pipeline at 400 DPI (or
  higher if the source PDF is high-res) until the final PDF write — don't
  downsample and re-upsample along the way.
- If the source PDF is vector (not a scanned image) and pypdfium2 renders
  it crisply at high DPI, that's fine — the important thing is the final
  raster going into the PDF is high resolution, not that it stayed vector.
