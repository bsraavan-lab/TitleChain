# TitleChain

TitleChain turns an Encumbrance Certificate (EC) into a title-scrutiny-ready
chain report: the property's ownership/encumbrance graph, with every live encumbrance,
chain break, and search-window gap identified deterministically and traced back to its
source region on the page.

Built on Sarvam's Document Intelligence + LLM APIs, with every finding clickable back to
a cropped image of the exact table cell it came from.

## How it works

1. **Digitise** — the EC PDF/scan is sent to Sarvam DI, which returns per-page layout
   blocks (tables, paragraphs, headers) with bounding-box coordinates and confidence.
2. **Extract** — table blocks are parsed into typed encumbrance entries (survey number,
   parties, instrument, dates) via an LLM call against a fixed schema.
3. **Derive** — entries are assembled into an ownership/encumbrance chain, flagging
   breaks, gaps, and search-window insufficiency.
4. **Verify** — every derived finding links back to a pixel-cropped source region
   (`crops.py`, via `pypdfium2`) so nothing is asserted without evidence on the page.

See [docs/PRD.md](docs/PRD.md) for the full product spec, [docs/STACK.md](docs/STACK.md)
for stack decisions, and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for routes, job
states, and module contracts.

## Stack

- **Backend:** FastAPI + uvicorn, single process
- **Frontend:** Jinja2 + HTMX, server-rendered, no build step
- **Schema:** Pydantic v2
- **Digitisation/extraction:** Sarvam AI (`sarvamai` SDK + raw `httpx`)
- **Crops:** pypdfium2 + Pillow
- **Storage:** stdlib `sqlite3`, no ORM
- **Tests:** pytest

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your Sarvam API key into .env
```

## Run

```bash
uvicorn app.main:app --port 8077
```

Open `http://localhost:8077`.

## Test

```bash
pytest
```

## Project layout

```
app/            FastAPI app: routes, pipeline, extraction, crops, storage
docs/           PRD, architecture, stack decisions, rubric, customer journey
ec_samples/     Sample ECs used for development and integrity checks
tests/          pytest suite
assets/         Logo and static brand assets
config.py       Loads SARVAM_API_KEY from .env
run_di.py       CLI: run Sarvam DI on a single file
check_key.py    Verify the Sarvam API key loads and the SDK client builds
check_ec_integrity.py   Kill-test: verify DI output preserves load-bearing EC fields
```
