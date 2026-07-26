"""OURS — bbox → cropped PNG from the page raster.

Verified end to end (STACK.md): pypdfium2 renders ec2_pacollege.pdf p2 at exactly
3509 × 2480 — the same raster Sarvam digitised against — so stage-① coordinates
land with NO transform at scale = 3509 / max(page.get_size()).

Two views, because a crop with no context is as unfalsifiable as no crop at all:
  crop()      — the block itself
  page_rect() — the whole page with the same rectangle drawn on it

Rendering is lazy and cached per request path: never render a 40-page document up
front.
"""

from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

TARGET_LONG_EDGE = 3509  # the raster geometry Sarvam digitises PDFs against
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@lru_cache(maxsize=32)
def _render(pdf_path: str, page_num: int) -> Image.Image:
    # An image IS the raster Sarvam digitised (verified: DI reports ec2_scan-1.jpg
    # at exactly its own 1404×992), so it is returned untouched — scaling it would
    # break the very no-transform property the PDF path was chosen for.
    if Path(pdf_path).suffix.lower() in IMAGE_SUFFIXES:
        return Image.open(pdf_path).convert("RGB")
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_num - 1]
    scale = TARGET_LONG_EDGE / max(page.get_size())
    return page.render(scale=scale).to_pil().convert("RGB")


def _png(img: Image.Image, max_width: int = 1600) -> bytes:
    if img.width > max_width:
        h = int(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def crop(pdf_path: str | Path, page_num: int, bbox: tuple[float, float, float, float]) -> bytes:
    """bbox straight from the block JSON — no transform."""
    img = _render(str(pdf_path), page_num)
    x1, y1, x2, y2 = (int(v) for v in bbox)
    pad = 8
    box = (max(x1 - pad, 0), max(y1 - pad, 0),
           min(x2 + pad, img.width), min(y2 + pad, img.height))
    return _png(img.crop(box))


def page_rect(pdf_path: str | Path, page_num: int,
              bbox: tuple[float, float, float, float] | None = None) -> bytes:
    """The full page, with the block's rectangle drawn on it.

    This is the answer to 'how do I know that crop is from entry 2 and not 3?'
    """
    img = _render(str(pdf_path), page_num).copy()
    if bbox:
        d = ImageDraw.Draw(img)
        x1, y1, x2, y2 = (int(v) for v in bbox)
        d.rectangle((x1, y1, x2, y2), outline=(190, 30, 45), width=10)
    return _png(img, max_width=1400)


def page_count(pdf_path: str | Path) -> int:
    if Path(pdf_path).suffix.lower() in IMAGE_SUFFIXES:
        Image.open(pdf_path).close()   # unreadable file still fails here, loudly
        return 1
    return len(pdfium.PdfDocument(str(pdf_path)))
