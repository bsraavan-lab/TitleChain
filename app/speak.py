"""The scripts explain.py writes, spoken — bulbul:v3, cache-first.

Raw httpx rather than the SDK, for the same reason extract.py went raw: the
request shape is small and known, and the SDK adds a surface we would have to
re-verify. Auth is the same `api-subscription-key` header the whole pipeline
uses.

Cache-first like digitise.py, and for the same reason: the same sentence is
never bought twice. The key is a hash of (model, voice, language, text), so a
correction that changes the script changes the key and the stale audio is
simply never asked for again — nothing to invalidate, nothing to garbage-
collect.

The API takes a LIST of inputs and returns one WAV per input. Long scripts are
split on sentence boundaries into chunks comfortably under the per-input limit
and stitched back together with the stdlib `wave` module — every chunk comes
back with identical parameters because it is one voice at one sample rate, so
concatenating frames is lossless.
"""

from __future__ import annotations

import base64
import hashlib
import io
import re
import time
import wave
from dataclasses import dataclass

import httpx

from . import paths

TTS_URL = "https://api.sarvam.ai/text-to-speech"
MODEL = "bulbul:v3"
SPEAKER = "shreya"                  # calm narration — findings, not a jingle
SAMPLE_RATE = 24000
LANG_CODES = {"en": "en-IN", "ta": "ta-IN", "hi": "hi-IN"}

# Comfortably under bulbul's per-input ceiling, and short enough that the first
# chunk of a long script starts synthesising fast.
CHUNK_CHARS = 450
INPUTS_PER_CALL = 3


@dataclass
class Spoken:
    audio: bytes                    # a complete WAV file
    cached: bool
    ms: int
    chars: int


def cache_key(text: str, lang: str) -> str:
    raw = f"{MODEL}|{SPEAKER}|{lang}|{text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _cache_path(key: str):
    # paths.OUTPUT is read at call time, not import time, so the test fixtures'
    # reload of paths moves this cache with everything else.
    return paths.OUTPUT / "speech" / f"{key}.wav"


def chunks(text: str) -> list[str]:
    """Sentence-boundary packing. A chunk never splits mid-sentence, because a
    synthesis boundary mid-clause is audible as a wrong breath."""
    sentences = [s for s in re.split(r"(?<=[.!?।])\s+", text.strip()) if s]
    out: list[str] = []
    current = ""
    for s in sentences:
        candidate = f"{current} {s}".strip()
        if current and len(candidate) > CHUNK_CHARS:
            out.append(current)
            current = s
        else:
            current = candidate
    if current:
        out.append(current)
    return out or [text.strip()]


def _concat_wavs(parts: list[bytes]) -> bytes:
    if len(parts) == 1:
        return parts[0]
    frames: list[bytes] = []
    params = None
    for p in parts:
        with wave.open(io.BytesIO(p)) as w:
            if params is None:
                params = w.getparams()
            frames.append(w.readframes(w.getnframes()))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setparams(params)
        for f in frames:
            w.writeframes(f)
    return buf.getvalue()


def synthesise(text: str, lang: str) -> Spoken:
    """Text in, WAV out. Raises on network/API failure — the route decides what
    an honest failure sounds like; this module never fabricates silence."""
    key = cache_key(text, lang)
    path = _cache_path(key)
    if path.is_file():
        return Spoken(audio=path.read_bytes(), cached=True, ms=0, chars=len(text))

    # Imported here so the app still boots — and serves cached audio — on a
    # machine with no API key configured. Same posture as digitise.py.
    from config import get_api_key

    pieces = chunks(text)
    audios: list[bytes] = []
    started = time.monotonic()
    for i in range(0, len(pieces), INPUTS_PER_CALL):
        batch = pieces[i:i + INPUTS_PER_CALL]
        resp = httpx.post(
            TTS_URL,
            headers={"api-subscription-key": get_api_key()},
            json={
                "inputs": batch,
                "target_language_code": LANG_CODES.get(lang, "en-IN"),
                "speaker": SPEAKER,
                "model": MODEL,
                "speech_sample_rate": SAMPLE_RATE,
                # Reads "2520/2019", dates and code-mixed clauses out properly
                # instead of spelling them.
                "enable_preprocessing": True,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        audios.extend(base64.b64decode(a) for a in resp.json()["audios"])
    ms = int((time.monotonic() - started) * 1000)

    audio = _concat_wavs(audios)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return Spoken(audio=audio, cached=False, ms=ms, chars=len(text))
