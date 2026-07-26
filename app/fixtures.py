"""Entries transcribed from the REAL stage-① output in output/ec2_pacollege-ta-IN/.

Every value below — including the two `None` date fields on entry 2 — is what
Sarvam actually returned. Entry 2's dates were dropped inside a block reporting
0.962 confidence; that is the real failure R9 exists to catch, and it is left in
deliberately. Do not "fix" it.

This module stands in for extract.py (stage ②) until 105B typing is wired. The
frontend never knows the difference: both produce list[Entry].
"""

from __future__ import annotations

from .models import ECHeader, Entry, Party, PRNumber, Schedule, Source

BLOCK_P1 = "20260725_14a106f7-b9b8-4f8b-82de-a4f611e4652c_1_block_003"
BLOCK_P2 = "20260725_14a106f7-b9b8-4f8b-82de-a4f611e4652c_2_block_000"

TRUST = "அருள்ஜோதி சாரிடபிள் டிரஸ்ட்"
COLLEGE = "பி ஏ காலேஜ் ஆப் என்ஜினியரிங் அண்ட் டெக்னாலஜி"
APPU = "அப்புக்குட்டி"


def _parties(names: list[tuple[str, str | None]]) -> list[Party]:
    return [Party(name_native=n, role_marker=m) for n, m in names]


EC2_HEADER = ECHeader(
    sro="Pollachi",
    village="Puliyampatti",
    survey_details=["95/2", "100/3A", "101/3", "116/A1", "116/B3", "113/1B"],
    search_period_start="01-Jan-2018",
    search_period_end="18-Jun-2023",
    issue_date="19-Jun-2023",
    declared_entry_count=2,
)

EC2_ENTRIES: list[Entry] = [
    Entry(
        sr_no=1,
        doc_no="2520/2019",
        doc_year=2019,
        date_execution="12-Mar-2019",
        date_presentation="12-Mar-2019",
        date_registration="12-Mar-2019",
        nature="Lease deed",
        executants=_parties([(TRUST, "முத."), (APPU, "முக.")]),
        claimants=_parties([(COLLEGE, "முத."), (APPU, "முக.")]),
        volume_page="-",
        consideration_value="-",
        market_value="ரூ. 3,60,000/-",
        pr_numbers=[
            PRNumber(doc_no="4451/2005", year=2005),
            PRNumber(doc_no="4453/2005", year=2005),
            PRNumber(doc_no="4581/2007", year=2007),
            PRNumber(doc_no="4582/2007", year=2007),
            PRNumber(doc_no="4755/2011", year=2011),
        ],
        remarks=None,
        schedules=[
            Schedule(
                property_type="Agriculture Land with Building",
                extent=None,
                village_street="Puliyampatti",
                survey_nos=["100/3A", "113/1B", "116/A1", "116/B1", "95/2"],
                door_no="2/340A",
                boundaries_native=None,
            )
        ],
        source=Source(page_num=1, block_id=BLOCK_P1,
                      bbox=[326.0, 1047.0, 3216.0, 2329.0], confidence=0.952),
    ),
    Entry(
        sr_no=2,
        doc_no="8756/2020",
        doc_year=2020,
        # ── the real stage-① miss: all three date cells dropped. R9 fires here. ──
        date_execution=None,
        date_presentation=None,
        date_registration=None,
        nature="Cancellation Deed",
        executants=_parties([(TRUST, "முத."), (APPU, "முக.")]),
        claimants=_parties([(COLLEGE, "முத."), (APPU, "முக.")]),
        volume_page="-",
        consideration_value="-",
        market_value="ரூ. 12,000/-",
        pr_numbers=[PRNumber(doc_no="2520/2019", year=2019)],
        remarks="This document cancels the document R/பொள்ளாச்சி/புத்தகம் 1/2520/2019",
        schedules=[
            Schedule(
                property_type=None,
                extent=None,
                village_street="Puliyampatti",
                survey_nos=["100/3A", "113/1B", "116/A1", "116/B1", "95/2"],
                door_no="2/340A",
                boundaries_native=(
                    "கிழக்கு - க,ச,101/3 அருள்ஜோதி சாரிடபிள் டிரஸ்ட் மீதி பூமி, "
                    "மேற்கு - க,ச,117 விஜயேஸ்வரி டெக்ஸ்டைல்ஸ்"
                ),
            )
        ],
        source=Source(page_num=2, block_id=BLOCK_P2,
                      bbox=[308.0, 114.0, 3208.0, 1342.0], confidence=0.9621813893318176),
    ),
]


# The pipeline no longer reads header/entries from here — stage ② types them for
# real (extract.py). EC2_HEADER/EC2_ENTRIES above remain as the hand-verified
# ground truth that tests/test_rulebook.py runs the rulebook against.
SAMPLES: dict[str, dict] = {
    "pollachi": {
        "label": "Pollachi · 2018–23",
        "pdf": "ec_samples/ec2_pacollege.pdf",
        "cached_di": "output/ec2_pacollege-ta-IN",
    },
    "uthukuli": {
        "label": "Uthukuli · 2024–25",
        "pdf": "ec_samples/ec3_rera.pdf",
        "cached_di": "output/ec3_rera-ta-IN",
    },
}
