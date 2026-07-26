"""Stage ① — pixels → structure. Sarvam Document Intelligence, `sarvamai` SDK.

In: a scanned Tamil EC (PDF or image). Out: one `Page` per page, each carrying
the blocks Sarvam found — `block_id`, `coordinates`, `layout_tag`, `confidence`,
`reading_order`, `text` (table HTML).

Three constraints shape this file, all of them real (PIPELINE §①):

  10 pages per job  → `_chunks()` splits, and page numbers are re-based onto the
                      original document so a bbox always names the page the
                      advocate is looking at.
  10 requests/min   → `_throttle()` spaces job creation.
  async only        → the SDK's `wait_until_complete()` blocks; we are already on
                      a background thread, so that is the right shape.

Cache-first, and not only to save money: `output/` already holds three real
digitisations, so the demo survives a total Sarvam outage, and re-running a case
never re-bills a page. The cache is keyed on the file's SHA-1, so a re-upload
under a different name is still a hit.

Failure is visible, never silent. A chunk that will not digitise after one retry
becomes an `UnreadChunk` — the pages it covers are reported as unread rather than
quietly missing from the certificate.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
LANGUAGE = "ta-IN"
PAGES_PER_JOB = 10          # hard API cap
MIN_JOB_INTERVAL = 6.5      # 10 req/min, with headroom

Progress = Callable[[int, str], None]   # (pages_done, detail)


# ── what stage ① produces ────────────────────────────────────────────────────

@dataclass
class Block:
    block_id: str
    page_num: int
    bbox: list[float] | None
    layout_tag: str | None
    confidence: float | None
    reading_order: int | None
    text: str


@dataclass
class Page:
    page_num: int
    width: int | None            # the raster Sarvam measured its bboxes against
    height: int | None
    blocks: list[Block] = field(default_factory=list)

    @property
    def tables(self) -> list[Block]:
        return [b for b in self.blocks if (b.layout_tag or "") == "table"]


@dataclass
class UnreadChunk:
    page_from: int
    page_to: int
    reason: str


@dataclass
class Digitised:
    pages: list[Page]
    markdown: str
    source_dir: Path
    from_cache: bool
    unread: list[UnreadChunk] = field(default_factory=list)

    @property
    def blocks(self) -> list[Block]:
        return [b for p in self.pages for b in p.blocks]

    def block(self, block_id: str) -> Block | None:
        return next((b for b in self.blocks if b.block_id == block_id), None)

    def page(self, page_num: int) -> Page | None:
        return next((p for p in self.pages if p.page_num == page_num), None)


# ── reading a digitisation off disk ──────────────────────────────────────────

def _parse_page_json(raw: dict, page_offset: int = 0) -> Page:
    """One `metadata/page_NNN.json` → a Page.

    `page_offset` re-bases a chunk's page numbers onto the original document:
    page 2 of chunk 2 is page 12 of the certificate, and the advocate only ever
    hears about page 12.
    """
    blocks: list[Block] = []
    page_num = int(raw.get("page_num", 1)) + page_offset
    for b in raw.get("blocks", []):
        c = b.get("coordinates") or {}
        bbox = ([float(c["x1"]), float(c["y1"]), float(c["x2"]), float(c["y2"])]
                if {"x1", "y1", "x2", "y2"} <= c.keys() else None)
        blocks.append(Block(
            block_id=b.get("block_id", ""),
            page_num=page_num,
            bbox=bbox,
            layout_tag=b.get("layout_tag"),
            confidence=b.get("confidence"),
            reading_order=b.get("reading_order"),
            text=b.get("text", ""),
        ))
    blocks.sort(key=lambda b: (b.reading_order if b.reading_order is not None else 1e9))
    return Page(page_num=page_num, width=raw.get("image_width"),
                height=raw.get("image_height"), blocks=blocks)


def read_dir(out_dir: Path, page_offset: int = 0) -> tuple[list[Page], str]:
    """Load an extracted DI output directory. This is also the cache reader."""
    pages = [
        _parse_page_json(json.loads(f.read_text(encoding="utf-8")), page_offset)
        for f in sorted((out_dir / "metadata").glob("page_*.json"))
    ]
    md_files = sorted(out_dir.rglob("*.md"))
    markdown = "\n\n".join(f.read_text(encoding="utf-8") for f in md_files)
    return pages, markdown


# ── cache ────────────────────────────────────────────────────────────────────

def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _is_complete(d: Path) -> bool:
    return d.is_dir() and any((d / "metadata").glob("page_*.json"))


def find_cached(path: Path, language: str = LANGUAGE) -> Path | None:
    """SHA-1 first, then the filename convention the three staged samples use.

    The stem fallback is what lets `uploads/1785046108_ec2_scan-1.jpg` find
    `output/ec2_scan-ta-IN/` — the upload path prefixes a timestamp, and the
    cached digitisation predates it.
    """
    if not OUTPUT.is_dir():
        return None

    digest = sha1(path)
    for d in sorted(OUTPUT.iterdir()):
        marker = d / ".source_sha1"
        if marker.is_file() and marker.read_text().strip() == digest and _is_complete(d):
            return d

    stem = path.stem
    for candidate_stem in (stem, stem.split("_", 1)[-1]):
        # uploads/ prefixes a timestamp; the cached digitisation predates it
        d = OUTPUT / f"{candidate_stem}-{language}"
        if _is_complete(d):
            return d
    # NOT matched: a single page-image of a multi-page scan ("ec2_scan-1.jpg")
    # against the whole bundle's digitisation — its entries would cite page 2 of
    # a one-page file. A false cache miss costs ₹0.5; that mismatch costs trust.
    return None


# ── splitting, for the 10-page cap ───────────────────────────────────────────

def _chunks(path: Path, pages: int) -> list[tuple[Path, int]]:
    """[(file to send, page offset)] — the identity for anything ≤ 10 pages."""
    if pages <= PAGES_PER_JOB or path.suffix.lower() != ".pdf":
        return [(path, 0)]

    src = pdfium.PdfDocument(str(path))
    tmp = OUTPUT / ".chunks" / path.stem
    tmp.mkdir(parents=True, exist_ok=True)
    out: list[tuple[Path, int]] = []
    for start in range(0, pages, PAGES_PER_JOB):
        idx = list(range(start, min(start + PAGES_PER_JOB, pages)))
        doc = pdfium.PdfDocument.new()
        doc.import_pages(src, idx)
        chunk_path = tmp / f"{path.stem}_p{start + 1}-{idx[-1] + 1}.pdf"
        buf = io.BytesIO()
        doc.save(buf)
        chunk_path.write_bytes(buf.getvalue())
        out.append((chunk_path, start))
    return out


_last_job_at = 0.0


def _throttle() -> None:
    global _last_job_at
    wait = MIN_JOB_INTERVAL - (time.monotonic() - _last_job_at)
    if wait > 0:
        time.sleep(wait)
    _last_job_at = time.monotonic()


# ── the call ─────────────────────────────────────────────────────────────────

def _run_job(client, src: Path, dest: Path, language: str) -> tuple[list[Page], str, int]:
    """One DI job, start → download → extract. Returns (pages, markdown, offset-less)."""
    _throttle()
    job = client.document_intelligence.create_job(language=language, output_format="md")
    job.upload_file(str(src))
    job.start()
    status = job.wait_until_complete()
    state = getattr(status, "job_state", None)
    if state not in ("Completed", "COMPLETED", "completed"):
        raise RuntimeError(f"digitisation job ended in state {state!r}")

    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "output.zip"
    job.download_output(str(zip_path))
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)
    pages, markdown = read_dir(dest)
    return pages, markdown, 0


def digitise(path: Path, *, pages_total: int, language: str = LANGUAGE,
             on_progress: Progress | None = None,
             allow_network: bool = True) -> Digitised:
    """Stage ①. Cache first; call Sarvam only for what is genuinely new."""
    say = on_progress or (lambda done, detail: None)

    cached = find_cached(path, language)
    if cached:
        pages, markdown = read_dir(cached)
        say(len(pages), f"Reading {len(pages)} pages (cached digitisation)")
        return Digitised(pages=pages, markdown=markdown, source_dir=cached,
                         from_cache=True)

    if not allow_network:
        raise RuntimeError("no cached digitisation for this file and network is off")

    # imported here so the app still boots — and serves cached cases — on a
    # machine with no API key configured
    from sarvamai import SarvamAI

    from config import get_api_key

    client = SarvamAI(api_subscription_key=get_api_key())
    dest_root = OUTPUT / f"{path.stem}-{language}"
    dest_root.mkdir(parents=True, exist_ok=True)

    chunks = _chunks(path, pages_total)
    all_pages: list[Page] = []
    md_parts: list[str] = []
    unread: list[UnreadChunk] = []

    for n, (chunk_path, offset) in enumerate(chunks, start=1):
        first, last = offset + 1, min(offset + PAGES_PER_JOB, pages_total)
        label = (f"Reading pages {first}–{last} of {pages_total}"
                 if len(chunks) > 1 else f"Reading page 1 of {pages_total}")
        say(len(all_pages), label)

        dest = dest_root if len(chunks) == 1 else dest_root / f"chunk_{n:02d}"
        last_error: Exception | None = None
        for attempt in (1, 2):                       # retry once, then give up loudly
            try:
                pages, markdown, _ = _run_job(client, chunk_path, dest, language)
                for p in pages:
                    p.page_num += offset
                    for b in p.blocks:
                        b.page_num += offset
                all_pages.extend(pages)
                md_parts.append(markdown)
                last_error = None
                break
            except Exception as exc:                 # noqa: BLE001 — reported, not swallowed
                last_error = exc
                if attempt == 1:
                    time.sleep(3)

        if last_error is not None:
            unread.append(UnreadChunk(first, last, str(last_error)[:200]))
        say(len(all_pages), label)

    (dest_root / ".source_sha1").write_text(sha1(path))
    return Digitised(pages=sorted(all_pages, key=lambda p: p.page_num),
                     markdown="\n\n".join(md_parts), source_dir=dest_root,
                     from_cache=False, unread=unread)


def cleanup_chunks() -> None:
    shutil.rmtree(OUTPUT / ".chunks", ignore_errors=True)
