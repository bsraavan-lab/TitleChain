"""Stage ② — structure → typed records. `sarvam-105b`, raw httpx, strict schema.

Why httpx and not the SDK: `sarvamai`'s `chat.completions()` exposes no
`response_format` parameter at all (checked against 0.1.28 — the signature carries
`tools`/`tool_choice` and nothing that would hold a JSON schema). Strict typing is
the entire point of this stage, so the request body is built here by hand, where
it is visible and editable. STACK.md called this one correctly.

The schema is not written twice. It is `models.Entry.model_json_schema()` with the
fields the model must not invent removed. One Pydantic definition, three uses.

Two measured facts shape this file, and neither was in the plan:

  · **`max_tokens` is capped at 4096** on the starter tier (measured — the API
    rejects 16000 by name). A 40-entry certificate cannot be typed in one reply
    at any prompt quality, so entries are typed **one stage-① table block per
    call** and merged by `sr_no`. Chunking here is not an optimisation, it is the
    only shape that fits.

  · **105B is a reasoning model.** Left alone it spends the whole 4096-token
    budget on `reasoning_content` and returns `content: null` — a silent empty
    success. `/no_think` in the system turn cuts that to roughly 2000 tokens and
    lets content through; `finish_reason == "length"` is checked explicitly so a
    truncated reply can never be mistaken for a short certificate.

Because we chunk by block, **the model is never asked for its own provenance.**
It receives one block and returns the entries in it; `source` is attached from the
block we sent. A hallucinated block id is not a bug we have to detect — it is not
a value the model is allowed to write.

The model's job is deliberately tiny, and the prompt says so: transcriber, not
analyst. An unreadable cell becomes `null`, because the honest null is what R9
reads — a model that helpfully guesses a missing date destroys the only signal
that would have caught stage-①'s dropped cell.
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx
from pydantic import ValidationError

from .digitise import Block, Digitised, UnreadChunk
from .models import ECHeader, Entry

BASE_URL = "https://api.sarvam.ai/v1/chat/completions"
EXTRACT_VERSION = "e3"       # bump when prompts/schema change → extraction caches invalidate
PRIMARY_MODEL = "sarvam-105b"
FALLBACK_MODEL = "sarvam-30b"
SEED = 7                     # fixed → a re-run is reproducible, so disagreement is signal
MAX_TOKENS = 4096            # starter tier's hard ceiling, measured not assumed
MIN_CALL_INTERVAL = 1.0
MAX_PARALLEL = 4             # blocks are independent; 105B is slow, not cheap to wait on
TIMEOUT = httpx.Timeout(240.0, connect=15.0)

Progress = Callable[[str], None]


# ── schemas ──────────────────────────────────────────────────────────────────

def _strict(node: Any) -> Any:
    """Make a Pydantic schema acceptable to strict json_schema mode.

    Every object closes and every property is required. Optionality is carried by
    `anyOf: [T, null]` — which is the distinction we want: the model must *say*
    null, not omit the field.
    """
    if isinstance(node, list):
        return [_strict(v) for v in node]
    if not isinstance(node, dict):
        return node
    out = {k: _strict(v) for k, v in node.items() if k not in ("default", "title")}
    if out.get("type") == "object" and "properties" in out:
        out["additionalProperties"] = False
        out["required"] = list(out["properties"].keys())
    return out


def entries_schema() -> dict:
    """`{entries: [...]}` — Entry minus every field the model must not author.

    The pruning is not tidiness, it is budget. With 4096 output tokens shared with
    the model's own reasoning, each field we ask for competes with the fields that
    matter. So we drop:

      · `source`, `db_id`  — ours (see the module docstring)
      · `Party.name_roman` — names.py's, per models.py
      · everything in `Schedule` except `survey_nos` — store.py persists only
        `survey_nos`; `boundaries_native` alone is a paragraph of Tamil that is
        written to no column and read by no rule. Paying output tokens for a value
        that is discarded on save is how the entry that matters gets truncated.
    """
    entry = Entry.model_json_schema(ref_template="#/$defs/{model}")
    defs = entry.pop("$defs", {})
    defs.pop("Source", None)
    for ours in ("db_id", "source"):
        entry["properties"].pop(ours, None)
    defs.get("Party", {}).get("properties", {}).pop("name_roman", None)

    schedule = defs.get("Schedule", {}).get("properties", {})
    for unpersisted in ("property_type", "extent", "village_street", "door_no",
                        "boundaries_native"):
        schedule.pop(unpersisted, None)

    return _strict({
        "type": "object",
        "properties": {"entries": {"type": "array", "items": entry}},
        "$defs": defs,
    })


def header_schema() -> dict:
    h = ECHeader.model_json_schema()
    h.pop("$defs", None)
    h["properties"].pop("declared_entry_count", None)   # ours — see declared_count()
    return _strict(h)


# ── OURS: which blocks are registration entries, and how many there should be ─

_SR_NO_HEADER = re.compile(r"வ\.?\s*<br\s*/?>?\s*எண்|Sr\.?\s*<br\s*/?>?\s*No", re.I)
_NUMBERED_ROW = re.compile(r'<td[^>]*rowspan="\d+"[^>]*>\s*(\d{1,3})\s*</td>')
_DOC_NO_CELL = re.compile(r"<td[^>]*>\s*\d{1,6}/(?:19|20)\d{2}\s*</td>")


def is_entry_table(b: Block) -> bool:
    """A registration table, or a continuation of one — not the header table.

    Deterministic on purpose. Sending the SRO/village header table to the entry
    pass is what produced an "entry" whose document number was the PDF's filename:
    asked for entries, a model returns entries. The cheapest fix is to not ask.

    Two shapes count, because a numbered entry spans pages:
      · the table carrying the `Sr.No./வ.எண்` column heading
      · a table opening with a row-spanning serial-number cell (the continuation)
    """
    if (b.layout_tag or "") != "table":
        return False
    return bool(_SR_NO_HEADER.search(b.text)
                or _NUMBERED_ROW.search(b.text)
                or _DOC_NO_CELL.search(b.text))


_COUNT = re.compile(r"(?:Number of Entries|பதிவுகளின்\s*எண்ணிக்கை)\s*[:：]?\s*(\d{1,4})")


def declared_count(dig: Digitised) -> int | None:
    """The certificate's own stated entry count — read by regex, not by the model.

    R10 compares this against how many entries we extracted, so it is only a
    checksum if it is produced *independently of the extraction*. Ask the same
    model that typed the entries how many entries there are and a pass that
    silently dropped one can report a count that matches its own mistake. A regex
    over the digitised text cannot collude with the typing pass.

    It also lives where the header pass would never look: on the last page of
    entries, tagged `footnote`.
    """
    for b in dig.blocks:
        m = _COUNT.search(b.text)
        if m:
            return int(m.group(1))
    return None


# ── prompts ──────────────────────────────────────────────────────────────────

_RULES = """You are a TRANSCRIBER, not an analyst. Obey these rules exactly:

1. COPY values from the document. Never interpret, summarise, translate, explain,
   or resolve a contradiction. If two cells disagree, copy what each one says.
2. Tamil text stays VERBATIM in every *_native field. Never transliterate or
   translate a person's or an organisation's name.
3. If a value is absent, illegible, or you are not certain of it, write null.
   NEVER infer, guess, or reconstruct a plausible value. A null is a correct
   answer; an invented date is a defect.
4. Dates: copy as they appear, changing only the format, to DD-MMM-YYYY
   (e.g. 12-Mar-2019). An empty or unreadable date cell is null."""

# `/no_think` is load-bearing, not a stylistic hint — see the module docstring.
SYSTEM_ENTRIES = f"""/no_think
You transcribe entries from a Tamil Nadu Encumbrance Certificate (EC) into JSON.

{_RULES}
5. One object per numbered EC entry — the வ.எண் / Sr. No. cell, usually the
   left-most cell with a rowspan. Return the entries in this block and no others.
6. Sub-rows — Consideration Value / கைமாற்றுத் தொகை, Market Value / சந்தை மதிப்பு,
   PR Number / முந்தைய ஆவண எண், Document Remarks / ஆவணக் குறிப்புகள், Schedule
   details — belong to the numbered entry they sit under.
7. PR numbers and the remarks text must be copied EXACTLY, in order. They are the
   links between documents and the whole purpose of this extraction. A PR number
   looks like 2520/2019: copy both parts.
   `doc_no` is the Document No. & Year column and always looks like 8756/2020.
   A bare "-" is NEVER a document number — it belongs to columns like Volume/Page
   or Consideration Value. If the document-number cell itself is missing, null.
8. `executants` are the parties in the executant column, `claimants` those in the
   claimant column. A cell often holds SEVERAL parties, numbered or on separate
   lines — return one object per party, never one object for the whole cell.
   In `name_native` put the name ONLY: strip the trailing role marker and any
   leading "1." numbering. Put the marker — முத. (executant) or முக. (minor /
   guardian) — in `role_marker` on its own, or null if the name carries none.
9. `schedules[].survey_nos` are the survey numbers in the Schedule details
   (சர்வே எண் / புல எண்), each copied as its own string, e.g. "116/A1".
10. If this block is NOT a registration-entry table — a header, a helpline, a
   disclaimer, a signature — return `{{"entries": []}}`. Never invent an entry from
   a table that has none, and never use the document's filename as a value.

Return only the JSON object described by the schema."""

SYSTEM_HEADER = f"""/no_think
You read the header of a Tamil Nadu Encumbrance Certificate (EC) into JSON.

{_RULES}
5. `survey_details` are the survey numbers the certificate says it searched
   (சர்வே விவரம் / புல எண்), each copied as its own string, in order.
6. `search_period_start` / `search_period_end` are the two ends of the search
   period (தேடுதல் காலம்), which is usually written as one "from - to" range.
7. `issue_date` is the certificate's own date (நாள்).

Return only the JSON object described by the schema."""

CONTINUATION_NOTE = (
    "The block below may continue an entry that began earlier; the immediately "
    "preceding block is shown first as CONTEXT ONLY. Do not return entries whose "
    "Sr. No. cell appears only in the context block.\n\n"
)


# ── the call ─────────────────────────────────────────────────────────────────

@dataclass
class Refusal:
    """Stage ② found nothing it could type. These are checks that RAN and failed —
    the refusal screen must never claim a check it did not make."""
    checks: list[str]
    detail: str


@dataclass
class Extraction:
    header: ECHeader
    entries: list[Entry]
    unread: list[UnreadChunk] = field(default_factory=list)


# Truncation is STOCHASTIC (measured): the identical request truncates on one call
# and stops cleanly on the next, because the reasoning burn varies run to run even
# at temperature 0 with a fixed seed. So the ladder is dice rolls, each rung a
# different configuration — reasoning effort, seed, model — ordered cheap-hope
# first. Six rungs because a marginal block (ec3_rera p5, 3286 chars, one entry)
# was observed exhausting four.
LADDER: list[tuple[str, str, dict]] = [
    ("105b", PRIMARY_MODEL, {}),
    ("105b/low", PRIMARY_MODEL, {"reasoning_effort": "low"}),
    ("105b/low+s1", PRIMARY_MODEL, {"reasoning_effort": "low", "seed": SEED + 1}),
    ("105b/low+s2", PRIMARY_MODEL, {"reasoning_effort": "low", "seed": SEED + 2}),
    ("30b/low", FALLBACK_MODEL, {"reasoning_effort": "low"}),
    ("30b/low+s1", FALLBACK_MODEL, {"reasoning_effort": "low", "seed": SEED + 1}),
]


class Truncated(RuntimeError):
    """finish_reason == 'length'. The reply is incomplete and must not be parsed —
    a half-read block is exactly the 'partial entry emitted as complete' that
    PIPELINE.md forbids."""


_last_call_at = 0.0


def _throttle() -> None:
    global _last_call_at
    wait = MIN_CALL_INTERVAL - (time.monotonic() - _last_call_at)
    if wait > 0:
        time.sleep(wait)
    _last_call_at = time.monotonic()


def _post(api_key: str, model: str, system: str, user: str, schema: dict,
          name: str, extra: dict | None = None) -> str:
    _throttle()
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0,
        "seed": SEED,
        "max_tokens": MAX_TOKENS,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": schema},
        },
        **(extra or {}),
    }
    r = httpx.post(BASE_URL, json=payload, timeout=TIMEOUT,
                   headers={"api-subscription-key": api_key,
                            "Content-Type": "application/json"})
    if r.status_code >= 400:
        raise httpx.HTTPStatusError(f"{r.status_code}: {r.text[:400]}",
                                    request=r.request, response=r)
    choice = r.json()["choices"][0]
    content = choice.get("message", {}).get("content")
    if choice.get("finish_reason") == "length" or not content:
        raise Truncated(
            f"{model} returned no usable content "
            f"(finish_reason={choice.get('finish_reason')!r})")
    return content


def _loads(content: str) -> dict:
    """Strict mode should make this a plain json.loads. Should is not a plan."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def _call(api_key: str, system: str, users: str | list[str], schema: dict,
          name: str) -> dict:
    """Try each prompt variant on 105B, then on 30B.

    `users` is ordered longest-prompt-first. Retrying a *truncated* reply
    unchanged is pointless — the budget will run out in the same place — so the
    variants exist to shed input: with 4096 tokens shared between reasoning and
    output, a shorter prompt is the only lever that actually buys output room.
    Transient HTTP failures get one plain retry; truncation moves to the next
    variant instead.
    """
    variants = [users] if isinstance(users, str) else users
    errors: list[str] = []
    for i, user in enumerate(variants):
        for label, model, extra in LADDER:
            try:
                return _loads(_post(api_key, model, system, user, schema, name, extra))
            except Truncated as exc:
                errors.append(f"v{i}/{label}: {exc}")
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                errors.append(f"v{i}/{label}: {type(exc).__name__}: {exc}")
                time.sleep(1.5)
    raise RuntimeError("; ".join(errors))


# ── block → entries ──────────────────────────────────────────────────────────

def _block_text(b: Block, label: str) -> str:
    return f"### {label} — page {b.page_num}\n{b.text}\n"


SPLIT_THRESHOLD = 2600   # chars of table HTML a single call is trusted with

_TR = re.compile(r"<tr[\s>].*?</tr>|<tr>.*?</tr>", re.S)


def split_block(block: Block) -> list[Block]:
    """OURS. One oversized multi-entry table → one sub-block per numbered entry.

    The 4096-token ceiling is per CALL, so the unit of work has to be small
    enough to fit — and the certificate itself says where to cut: every entry
    opens with a row-spanning Sr.No. cell, and its sub-rows (values, PR, remarks,
    schedule) follow until the next one. Rows before the first numbered row
    (column headings, a continuation of the previous block's entry) stay with the
    first group.

    Provenance is untouched: every sub-block keeps the parent's block_id and
    bbox, because that IS the region the advocate will be shown. A 40-entry
    certificate becomes 40 small calls instead of one impossible one.
    """
    if len(block.text) <= SPLIT_THRESHOLD:
        return [block]
    rows = _TR.findall(block.text)
    if len(rows) < 2:
        return [block]

    groups: list[list[str]] = [[]]
    for row in rows:
        if _NUMBERED_ROW.search(row) and groups[-1]:
            groups.append([])
        groups[-1].append(row)
    if len(groups) < 2:
        return [block]

    return [
        Block(block_id=block.block_id, page_num=block.page_num, bbox=block.bbox,
              layout_tag=block.layout_tag, confidence=block.confidence,
              reading_order=block.reading_order,
              text="<table>\n<tbody>\n" + "\n".join(g) + "\n</tbody>\n</table>")
        for g in groups
    ]


# Fields `entries_schema()` prunes but `models.Entry` still requires. They are
# Optional-without-default, which in Pydantic v2 means required-and-nullable —
# exactly the "a model that quietly omits a field fails loudly" contract in
# models.py. We did not ask for these, so we supply the honest null ourselves
# rather than loosening the model and letting a real omission through silently.
_PRUNED_SCHEDULE = ("property_type", "extent", "village_street", "door_no",
                    "boundaries_native")


def _hydrate(raw: dict, block: Block) -> dict:
    """Model output → a dict `Entry.model_validate` will accept."""
    schedules = []
    for s in raw.get("schedules") or []:
        schedules.append({**{k: None for k in _PRUNED_SCHEDULE}, **s})
    return {
        **raw,
        "schedules": schedules,
        "source": {"page_num": block.page_num, "block_id": block.block_id,
                   "bbox": block.bbox, "confidence": block.confidence},
    }


_DOC_KEY = re.compile(r"(\d{1,6})\s*/\s*((?:19|20)\d{2})")
_TAG = re.compile(r"<[^>]+>")


def _detag(value: str | None) -> str | None:
    """Strip the markup the model faithfully copied along with the text.

    Stage ① emits table cells as HTML, so a name wrapped for column width arrives
    as "பி ஏ காலேஜ் ஆப்<br/>என்ஜினியரிங்". The model is right to copy it verbatim —
    rule 2 says never alter a name — but `<br/>` is the digitiser's line break, not
    part of anyone's name, and a name carrying it will never cluster or match.
    Removing presentation is ours to do; removing content is nobody's.
    """
    if value is None:
        return None
    return re.sub(r"\s+", " ", _TAG.sub(" ", value)).strip() or None


_LABELLED = re.compile(
    r"^\s*(?:S\.?R\.?O|Village|கிராமம்|சா\.ப\.அ|Survey\s*Details|சர்வே\s*விவரம்|"
    r"Date|நாள்|Search\s*Period|தேடுதல்\s*காலம்)\b[^:：]*[:：]\s*", re.I)


def _unlabel(value: str | None) -> str | None:
    """"S.R.O /சா.ப.அ: Pollachi" → "Pollachi".

    The header is a two-column table whose cells hold label and value together, so
    a verbatim copy is the label too. Only a known leading label is removed, and
    only from the front — a village whose name contains a colon keeps it.
    """
    if value is None:
        return None
    return _LABELLED.sub("", value).strip() or None


def normalise_header(h: ECHeader) -> ECHeader:
    h.sro, h.village = _unlabel(_detag(h.sro)), _unlabel(_detag(h.village))
    h.issue_date = _unlabel(_detag(h.issue_date))
    h.search_period_start = _unlabel(_detag(h.search_period_start))
    h.search_period_end = _unlabel(_detag(h.search_period_end))
    h.survey_details = [s for s in (_unlabel(_detag(x)) for x in h.survey_details) if s]
    return h


def _normalise(e: Entry) -> Entry:
    """OURS. Put document keys in the one form the graph can match on.

    `build_graph` resolves a PR pointer by `nodes.get(pr.doc_no)` against each
    entry's `doc_no`, and `store.load_entries` re-parses the year back out of the
    string — so "4451" and "4451/2005" are not two spellings of one value, they
    are a resolved edge and a dangling one. The model returns both forms across
    runs; which one you get decides whether R4 fires. That is far too load-bearing
    to leave to a prompt, so the year is reattached here, from the model's own
    `year` field, deterministically.

    Nothing is invented: a PR number with no year anywhere stays exactly as read.
    """
    for field_name in ("doc_no", "date_execution", "date_presentation",
                       "date_registration", "nature", "volume_page",
                       "consideration_value", "market_value", "remarks"):
        setattr(e, field_name, _detag(getattr(e, field_name)))
    for party in (*e.executants, *e.claimants):
        party.name_native = _detag(party.name_native) or party.name_native
        party.role_marker = _detag(party.role_marker)
    for sch in e.schedules:
        sch.survey_nos = [s for s in (_detag(x) for x in sch.survey_nos) if s]

    for pr in e.pr_numbers:
        if "/" not in pr.doc_no and pr.year:
            pr.doc_no = f"{pr.doc_no.strip()}/{pr.year}"
        elif (m := _DOC_KEY.search(pr.doc_no)):
            pr.doc_no = f"{m.group(1)}/{m.group(2)}"
    # An empty PR cell ("-") sometimes comes back as a PRNumber shell ("/", "-").
    # A pointer with no digits points at nothing — it would only manufacture a
    # phantom R4 dangling parent. And the same PR listed in both language columns
    # is one edge, not two: dedupe, order preserved.
    seen: set[str] = set()
    e.pr_numbers = [pr for pr in e.pr_numbers
                    if any(ch.isdigit() for ch in pr.doc_no)
                    and not (pr.doc_no in seen or seen.add(pr.doc_no))]

    if e.doc_no and (m := _DOC_KEY.search(e.doc_no)):
        e.doc_no = f"{m.group(1)}/{m.group(2)}"
        if e.doc_year is None:
            e.doc_year = int(m.group(2))
    return e


def _merge(into: Entry, extra: Entry) -> Entry:
    """An entry split across two blocks. First non-null wins; longer list wins.

    Never overwrite a value with a null: a continuation block genuinely does not
    contain the fields that were on the previous page, and its nulls are absence
    of evidence, not evidence of absence.
    """
    for name in type(into).model_fields:
        if name in ("sr_no", "source", "db_id"):
            continue
        cur, new = getattr(into, name), getattr(extra, name)
        if isinstance(cur, list):
            if len(new) > len(cur):
                setattr(into, name, new)
        elif cur is None and new is not None:
            setattr(into, name, new)
    return into


def extract(dig: Digitised, *, filename: str,
            on_progress: Progress | None = None,
            on_header: Callable[[ECHeader], Any] | None = None,
            api_key: str | None = None) -> Extraction | Refusal:
    """Stage ②. Typed records, or a Refusal naming the checks that actually failed.

    `on_header` fires the moment the header call returns — while entry blocks are
    still typing — so the caller can render the coverage ruler early. It receives
    the header without `declared_entry_count`; the final header on the result
    carries it.
    """
    say = on_progress or (lambda detail: None)

    if not any(p.tables for p in dig.pages):
        return Refusal(
            checks=["a registration-entry table"],
            detail="No table was found on any page of this document. An "
                   "Encumbrance Certificate presents its entries as a table.")

    tables = [sub for b in dig.blocks if is_entry_table(b) for sub in split_block(b)]
    if not tables:
        return Refusal(
            checks=["a registration-entry table", "a numbered-entry column"],
            detail="Tables were found, but none of them carries the numbered "
                   "registration-entry column an Encumbrance Certificate uses.")

    if api_key is None:
        from config import get_api_key
        api_key = get_api_key()

    entry_ids = {b.block_id for b in tables}
    schema = entries_schema()

    # ── one call per entry block, plus the header — all concurrent ───────────
    # Each block is independent by construction (continuation is handled by the
    # sr_no merge, not by conversation order), so the wall clock is one call deep
    # instead of len(tables) + 1. Worth doing: 105B is slow, and the advocate is
    # watching a progress line that has to keep moving.
    def header_task() -> ECHeader:
        page1 = dig.page(min(p.page_num for p in dig.pages))
        blocks = [b for b in (page1.blocks if page1 else [])
                  if b.block_id not in entry_ids]
        text = "\n".join(_block_text(b, f"BLOCK {i + 1}")
                         for i, b in enumerate(blocks))
        try:
            header = normalise_header(ECHeader.model_validate({
                **_call(api_key, SYSTEM_HEADER, f"Document: {filename}\n\n{text}",
                        header_schema(), "ec_header"),
                "declared_entry_count": None,
            }))
        except (RuntimeError, ValidationError):
            header = ECHeader(sro=None, village=None, survey_details=[],
                              search_period_start=None, search_period_end=None,
                              issue_date=None, declared_entry_count=None)
        if on_header:
            on_header(header.model_copy(deep=True))
        return header

    def _reclaim_doc_no(parsed: list[Entry], block: Block) -> None:
        """OURS. Recover a doc_no the model shifted out of its column.

        Observed at temperature 0: the same block yields doc_no "8756/2020" on
        one run and "-" on the next — the model slid one cell over. The real
        number is verifiably present in the block as a standalone `<td>` (the
        _DOC_NO_CELL shape matches only cells that ARE a document number, so PR
        cells with their label prefix never qualify). If exactly one such cell is
        claimed by no entry and exactly one entry has a junk doc_no, the pairing
        is forced, and we copy — from the block, not from imagination. Any
        ambiguity leaves the junk in place for R9 to flag.
        """
        candidates = {f"{m.group(1)}/{m.group(2)}"
                      for m in (_DOC_KEY.search(c) for c in
                                re.findall(r"<td[^>]*>\s*(\d{1,6}\s*/\s*(?:19|20)\d{2})\s*</td>",
                                           block.text))
                      if m}
        claimed = {e.doc_no for e in parsed}
        junk = [e for e in parsed if e.doc_no in (None, "-", "–")]
        unclaimed = candidates - claimed
        if len(junk) == 1 and len(unclaimed) == 1:
            junk[0].doc_no = unclaimed.pop()
            if junk[0].doc_year is None:
                junk[0].doc_year = int(junk[0].doc_no.split("/")[-1])

    def block_task(i: int, block: Block) -> tuple[list[Entry], UnreadChunk | None]:
        bare = f"Document: {filename}\n\n" + _block_text(block, "BLOCK TO TRANSCRIBE")
        prev = tables[i - 1] if i else None

        # The previous block is worth its tokens only when this one carries no
        # serial-number cell of its own — i.e. it is genuinely a continuation and
        # nothing else can say which entry these rows belong to. When the block
        # numbers itself, the sr_no merge already handles the split, and paying
        # ~1800 characters of input for context costs more output room than it
        # buys accuracy. Longest variant first; truncation falls back to `bare`.
        needs_context = prev is not None and not _NUMBERED_ROW.search(block.text)
        users = [bare]
        if needs_context:
            with_context = (f"Document: {filename}\n\n{CONTINUATION_NOTE}"
                            + _block_text(prev, "CONTEXT ONLY (already read)")
                            + _block_text(block, "BLOCK TO TRANSCRIBE"))
            users = [with_context, bare]
        try:
            raw = _call(api_key, SYSTEM_ENTRIES, users, schema, "ec_entries")
            parsed = [_normalise(Entry.model_validate(_hydrate(e, block)))
                      for e in raw.get("entries", [])]
            _reclaim_doc_no(parsed, block)
            return parsed, None
        except (RuntimeError, ValidationError, KeyError, TypeError) as exc:
            # Visible degradation. The pages this block covers are reported
            # unread rather than silently missing from the certificate.
            return [], UnreadChunk(block.page_num, block.page_num,
                                   f"could not be typed: {str(exc)[:160]}")

    done = 0
    say(f"Typing {len(tables)} entry blocks into the schema")

    results: dict[int, tuple[list[Entry], UnreadChunk | None]] = {}
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        head_future = pool.submit(header_task)
        futures = {pool.submit(block_task, i, b): i for i, b in enumerate(tables)}
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()
            done += 1
            say(f"Typing entries — {done} of {len(tables)} blocks read")
        header = head_future.result()

    # Merged in block order, never completion order, so the result is deterministic.
    by_sr: dict[int, Entry] = {}
    unread: list[UnreadChunk] = []
    for i in sorted(results):
        parsed, miss = results[i]
        if miss:
            unread.append(miss)
        for e in parsed:
            if e.sr_no in by_sr:
                _merge(by_sr[e.sr_no], e)
            else:
                by_sr[e.sr_no] = e

    if not by_sr:
        # A refusal is a statement ABOUT THE DOCUMENT — "this is not a certificate
        # I can read." If every block merely failed to come back, that statement is
        # false and defamatory to a perfectly good certificate: the fault is ours.
        # Raise, and let the pipeline mark it FAILED with the real reason.
        if len(unread) == len(tables):
            raise RuntimeError(
                "no entry block could be typed — "
                + "; ".join(u.reason for u in unread[:3]))
        return Refusal(
            checks=["a registration-entry table", "at least one numbered entry"],
            detail="Tables were found, but no numbered registration entry could be "
                   "read from any of them.")

    header.declared_entry_count = declared_count(dig)   # OURS — the R10 checksum
    return Extraction(header=header,
                      entries=[by_sr[k] for k in sorted(by_sr)],
                      unread=unread)


if __name__ == "__main__":
    print(json.dumps({"entries": entries_schema(), "header": header_schema()},
                     indent=2, ensure_ascii=False))
