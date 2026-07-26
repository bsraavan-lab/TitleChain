"""Kill-test checker: verify Sarvam DI output preserves the load-bearing EC fields.

Ground truth was read directly from the source PDFs (not from model output).
Usage: python3 check_ec_integrity.py <output_dir> <ec2|ec3>
"""

import re
import sys
import unicodedata
from pathlib import Path

# Anchors: the fields a title-chain product cannot survive losing.
# Each tuple: (label, list of acceptable regexes — any match counts)
GROUND_TRUTH = {
    "ec2": [
        ("doc_no entry 1 (2520/2019)", [r"2520\s*/\s*2019"]),
        ("doc_no entry 2 (8756/2020)", [r"8756\s*/\s*2020"]),
        ("nature 1: Lease deed", [r"[Ll]ease\s+[Dd]eed"]),
        ("nature 2: Cancellation Deed", [r"[Cc]ancellation\s+[Dd]eed"]),
        ("reg date 1 (12-Mar-2019)", [r"12[-/\s]*Mar[-/\s]*2019"]),
        ("reg date 2 (16-Oct-2020)", [r"16[-/\s]*Oct[-/\s]*2020"]),
        ("PR chain 4451/2005", [r"4451\s*/\s*2005"]),
        ("PR chain 4453/2005", [r"4453\s*/\s*2005"]),
        ("PR chain 4581/2007", [r"4581\s*/\s*2007"]),
        ("PR chain 4755/2011", [r"4755\s*/\s*2011"]),
        ("cross-ref: cancellation links 2520/2019", [r"cancel", r"ரத்து"]),
        ("market value 1 (3,60,000)", [r"3,?60,?000"]),
        ("market value 2 (12,000)", [r"12,?000"]),
        ("survey 100/3A", [r"100\s*/\s*3A"]),
        ("survey 113/1B", [r"113\s*/\s*1B"]),
        ("survey 116/A1", [r"116\s*/\s*A1"]),
        ("survey 95/2", [r"95\s*/\s*2"]),
        ("extent 10 ACRE 18 cents", [r"10\s*ACRE", r"18\.?0?\s*CENTS"]),
        ("door no 2/340A", [r"2\s*/\s*340\s*ஏ?A?"]),
        ("executant: அருள்ஜோதி சாரிடபிள் டிரஸ்ட்", [r"அருள்\s*ஜோதி", r"அருள்ஜோதி"]),
        ("claimant: பி ஏ காலேஜ்", [r"பி\s*ஏ\s*காலேஜ்", r"காலேஜ்\s*ஆப்"]),
        ("village Puliyampatti", [r"Puliyampatti", r"புலியம்பட்டி"]),
        ("SRO Pollachi", [r"Pollachi", r"பொள்ளாச்சி"]),
        ("entry count = 2", [r"எண்ணிக்கை\s*[:：]?\s*2", r"Number of Entries\D*2"]),
    ],
    "ec3": [
        ("doc_no 13698/2024", [r"13698\s*/\s*2024"]),
        ("nature: Gift deed", [r"[Gg]ift\s+[Dd]eed"]),
        ("reg date 30-Nov-2024", [r"30[-/\s]*Nov[-/\s]*2024"]),
        ("PR 14190/2023", [r"14190\s*/\s*2023"]),
        ("PR 15002/2023", [r"15002\s*/\s*2023"]),
        ("PR 8267/2024", [r"8267\s*/\s*2024"]),
        ("market value 1,300", [r"1,?300"]),
        ("survey 332/18A1", [r"332\s*/\s*18A1"]),
        ("survey 332/18B", [r"332\s*/\s*18B"]),
        ("survey 332/18C", [r"332\s*/\s*18C"]),
        ("schedule extent 1903.0 sq m", [r"1903\.?0?"]),
        ("schedule extent 390.24", [r"390\.24"]),
        ("schedule extent 716.85", [r"716\.85"]),
        ("schedule extent 727.65", [r"727\.65"]),
        ("schedule extent 738.45", [r"738\.45"]),
        ("schedule extent 247.5", [r"247\.50?"]),
        ("schedule extent 70.81", [r"70\.81"]),
        ("executant முகமது அன்சாரி", [r"முகமது\s*அன்சாரி", r"அன்சாரி"]),
        ("claimant chain (Governor/பேரூராட்சி)", [r"ஆளுநர்", r"பேரூராட்சி"]),
        ("village Uthukuli", [r"Uthukuli", r"ஊத்துக்குளி"]),
        ("property type Pathway", [r"Pathway"]),
        ("plot schedule 70.81 type Plot", [r"Plot"]),
    ],
}


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def main() -> None:
    out_dir, key = Path(sys.argv[1]), sys.argv[2]
    text = norm(
        "\n".join(
            f.read_text(errors="replace")
            for f in sorted(out_dir.rglob("*"))
            if f.suffix in {".md", ".html", ".json", ".txt"} and f.is_file()
        )
    )
    if not text.strip():
        sys.exit(f"no output text found under {out_dir}")

    anchors = GROUND_TRUTH[key]
    hits = []
    for label, patterns in anchors:
        ok = any(re.search(norm(p), text) for p in patterns)
        hits.append(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    n_ok = sum(hits)
    pct = 100.0 * n_ok / len(anchors)
    print(f"\n== {key}: {n_ok}/{len(anchors)} anchors intact = {pct:.0f}% ==")
    verdict = "FULL BUILD" if pct >= 90 else ("NARROW SCOPE" if pct >= 70 else "KILL/PIVOT")
    print(f"== verdict band: {verdict} ==")


if __name__ == "__main__":
    main()
