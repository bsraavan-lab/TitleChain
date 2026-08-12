"""What an entry means, said plainly — the script behind the speaker button.

No model writes these sentences. Every clause is a template filled from the same
typed objects the checklist and the report render, and the deed-type opener is
keyed on derive.nature_kind() — the SAME classifier the rulebook runs — so the
voice can never call something a lease that R2 is treating as a mortgage. A
wrong simplification of a legal instrument is a liability, not a UX bug, which
is why the one place an LLM could have gone here is the one place it isn't.

Two languages, one structure. The Tamil is spoken-register and code-switches the
way a Coimbatore advocate does across the desk — document numbers, dates and the
odd English legal term stay as written, because that is how they are said aloud
(bulbul's preprocessing reads them out). Findings are spoken from per-rule Tamil
templates where we have one, and in the rulebook's own English sentence where we
don't: an honest code-switch beats a guessed translation.

R4 never appears in the flags section: the parents sentence IS the R4 content,
composed from the same edges, and hearing "it points back to 4451/2005, which is
not here" twice in one breath teaches the ear to skim — the exact failure
runs_grouped exists to prevent on the checklist.
"""

from __future__ import annotations

from .derive import nature_kind
from .models import DerivedView, Entry, RuleRun, OUTCOME_ORDER

LANGS = ("en", "ta")

# How many findings one entry's script will speak. The worst two are the answer;
# a longer list is the checklist's job, and the button for that is on screen.
MAX_FLAGS = 2

# kind → (English opener, Tamil opener). {ex}/{cl} are the party lists; the verb
# is folded into the sentence per kind, because "gave it to" is right for a sale
# and wrong for a mortgage — the pledge runs the other way.
_KIND_EN: dict[str | None, str] = {
    "transfer":     "This entry records the property changing hands — {nature}. "
                    "{ex} passed it to {cl}.",
    "encumbrance":  "This entry is a mortgage or charge: {ex} pledged the "
                    "property to {cl} as security for money.",
    "discharge":    "This entry is a release: it records an earlier loan against "
                    "the property being closed.",
    "lease":        "This entry is a lease: {ex} let the property to {cl} for a "
                    "period, in return for rent.",
    "cancellation": "This entry cancels an earlier document — whatever that "
                    "document said no longer stands.",
    None:           "We could not classify what kind of document this entry is, "
                    "so read this one yourself — the page is one click away.",
}

_KIND_TA: dict[str | None, str] = {
    "transfer":     "இது சொத்து உரிமை மாறிய பதிவு — {nature}. {ex} இந்தச் "
                    "சொத்தை {cl}-க்கு கொடுத்திருக்கிறார்கள்.",
    "encumbrance":  "இது ஒரு அடைமானப் பதிவு: {ex} இந்தச் சொத்தை {cl}-இடம் "
                    "கடனுக்குப் பிணையாக வைத்திருக்கிறார்கள்.",
    "discharge":    "இது ஒரு விடுவிப்புப் பதிவு: முந்தைய கடன் ஒன்று "
                    "முடிக்கப்பட்டதைக் காட்டுகிறது.",
    "lease":        "இது ஒரு குத்தகைப் பதிவு: {ex} இந்தச் சொத்தை {cl}-க்கு "
                    "குத்தகைக்கு கொடுத்திருக்கிறார்கள்.",
    "cancellation": "இது ஒரு இரத்து ஆவணம் — முந்தைய ஆவணம் ஒன்றை ரத்து "
                    "செய்கிறது.",
    None:           "இந்தப் பதிவு என்ன வகை ஆவணம் என்று உறுதியாகச் சொல்ல "
                    "முடியவில்லை — இதை நீங்களே பக்கத்தில் படித்துப் பாருங்கள்.",
}

# rule_id → Tamil template for a spoken finding. {subject} is the run's own
# subject (a document number, mostly), which is language-neutral. Only the rules
# that fire per-entry today; anything else falls back to the English message.
_RULE_TA: dict[str, str] = {
    "R1":  "ஆவணம் {subject} பிறகு ரத்து செய்யப்பட்டிருக்கிறது — இது இப்போது "
           "உரிமையை நிரூபிக்காது.",
    "R2":  "இந்த அடைமானம் ({subject}) முடிக்கப்பட்டதற்கு எந்தப் பதிவும் "
           "இல்லை — சொத்தின் மேல் இந்தக் கடன் இன்னும் இருக்கலாம்.",
    "R9":  "இந்தப் பதிவில் சில கட்டங்களை எங்களால் படிக்க முடியவில்லை — "
           "பக்கத்தில் நேரடியாகப் பாருங்கள்.",
    "R10": "சான்றிதழ் சொல்லும் பதிவு எண்ணிக்கையும் நாங்கள் படித்த "
           "எண்ணிக்கையும் பொருந்தவில்லை.",
}


def _names(parties, lang: str) -> str:
    """Two names aloud, a count for the rest. Native script in BOTH languages:
    a name has one true form and it is the one on the page."""
    names = [p.name_native for p in parties if p.name_native]
    if not names:
        return "—" if lang == "en" else "பெயர் படிக்கப்படவில்லை"
    if len(names) <= 2:
        return (" and " if lang == "en" else " மற்றும் ").join(names)
    more = len(names) - 2
    if lang == "en":
        return f"{names[0]}, {names[1]} and {more} other{'s' if more > 1 else ''}"
    return f"{names[0]}, {names[1]} மற்றும் இன்னும் {more} பேர்"


def _open_runs_for(entry: Entry, view: DerivedView) -> list[RuleRun]:
    rank = {o: i for i, o in enumerate(OUTCOME_ORDER)}
    mine = [r for r in view.runs
            if r.is_open and r.rule_id != "R4"
            and entry.db_id in r.evidence_entry_ids]
    return sorted(mine, key=lambda r: (rank[r.outcome], r.rule_id, r.key))


def _flag_sentence(run: RuleRun, lang: str) -> str:
    if lang == "ta":
        template = _RULE_TA.get(run.rule_id)
        if template:
            return template.format(subject=run.subject)
    return run.message if run.message.endswith(".") else run.message + "."


def entry_script(entry: Entry, view: DerivedView, lang: str = "en") -> str:
    """The whole explanation, as one piece of text. Deterministic: same case,
    same words — which is also what lets speak.py cache the audio by content."""
    lang = lang if lang in LANGS else "en"
    parts: list[str] = []

    doc = entry.doc_no or ("no readable number" if lang == "en"
                           else "எண் படிக்கப்படவில்லை")
    when = entry.date_registration or entry.date_execution
    if lang == "en":
        opener = f"Entry {entry.sr_no} — document {doc}"
        opener += f", registered on {when}." if when else ". We could not read its date."
    else:
        opener = f"பதிவு {entry.sr_no} — ஆவணம் {doc}"
        opener += (f", {when} அன்று பதிவு செய்யப்பட்டது."
                   if when else ". இதன் தேதியைப் படிக்க முடியவில்லை.")
    parts.append(opener)

    kind = nature_kind(entry.nature)
    table = _KIND_EN if lang == "en" else _KIND_TA
    parts.append(table[kind].format(
        nature=entry.nature or "",
        ex=_names(entry.executants, lang), cl=_names(entry.claimants, lang)))

    value = entry.market_value or entry.consideration_value
    if value and value.strip() not in ("-", "—"):
        parts.append(f"The value on the page is {value}." if lang == "en"
                     else f"பக்கத்தில் உள்ள மதிப்பு: {value}.")

    parts.append(_parents_sentence(entry, view, lang))

    flags = _open_runs_for(entry, view)[:MAX_FLAGS]
    if flags:
        parts.append("Worth your attention:" if lang == "en"
                     else "கவனிக்க வேண்டியது:")
        parts.extend(_flag_sentence(r, lang) for r in flags)
    elif lang == "en":
        parts.append("Nothing else on this case is flagged against this entry.")
    else:
        parts.append("இந்தப் பதிவின் மேல் வேறு எந்தப் பிரச்சனையும் இந்த "
                     "கேஸில் குறிக்கப்படவில்லை.")

    return " ".join(p for p in parts if p)


def _parents_sentence(entry: Entry, view: DerivedView, lang: str) -> str:
    """The PR chain, spoken from the same edges the graph draws. An empty string
    when the entry names no parent — silence, not 'no parents', because the
    listener did not ask."""
    mine = [e for e in view.edges
            if e.edge_type == "PR_PARENT" and e.from_entry_id == entry.db_id]
    if not mine:
        return ""
    docs = [e.to_doc_no for e in mine]
    spoken = ", ".join(docs[:3]) + (
        ("" if len(docs) <= 3 else f" and {len(docs) - 3} more") if lang == "en"
        else ("" if len(docs) <= 3 else f" இன்னும் {len(docs) - 3}"))
    missing = sum(1 for e in mine if e.resolved_entry_id is None)

    if lang == "en":
        n = len(docs)
        head = (f"It points back to {n} earlier document{'s' if n > 1 else ''} — "
                f"{spoken}.")
        if missing == 0:
            return head + " All of them are in this case."
        if missing == n:
            return (head + " None of them is in this case, so nobody here has "
                    "read what is inside them.")
        return (head + f" {missing} of them {'are' if missing > 1 else 'is'} not "
                "in this case, so nobody here has read what is inside "
                f"{'them' if missing > 1 else 'it'}.")

    head = f"இந்த ஆவணம் {len(docs)} முந்தைய ஆவணத்தைக் குறிப்பிடுகிறது — {spoken}."
    if missing == 0:
        return head + " அவை எல்லாம் இந்த கேஸில் இருக்கின்றன."
    if missing == len(docs):
        return (head + " அவை எதுவும் இந்த கேஸில் இல்லை — அவற்றுக்குள் என்ன "
                "இருக்கிறது என்று இங்கே யாரும் படிக்கவில்லை.")
    return (head + f" இதில் {missing} ஆவணம் இந்த கேஸில் இல்லை — அதை இங்கே "
            "யாரும் படிக்கவில்லை.")


def case_script(view: DerivedView, lang: str = "en") -> str:
    """The whole case in four breaths: the verdict, the window, what is open,
    whether it can be signed. The Tamil is composed from the derivation's own
    numbers and states rather than translating the English verdict, because the
    verdict is a case-specific sentence and a guessed translation of a legal
    conclusion is the one thing this module refuses to produce."""
    lang = lang if lang in LANGS else "en"
    open_runs = view.open_runs
    ready = view.readiness.ready

    if lang == "en":
        parts = ["Here is where this case stands.", _as_sentence(view.verdict)]
        if view.coverage and view.coverage.detail:
            parts.append(_as_sentence(view.coverage.detail))
        n = len(open_runs)
        if n:
            parts.append(f"{n} item{'s' if n > 1 else ''} still need"
                         f"{'' if n > 1 else 's'} your attention — the first: "
                         f"{_as_sentence(open_runs[0].title)}")
        parts.append("Ready to sign off." if ready
                     else "Not ready to sign off yet.")
        return " ".join(parts)

    entries = sum(len(d.entries) for d in view.docs)
    parts = [f"இந்த கேஸின் நிலை இதுதான். {len(view.docs)} சான்றிதழ், "
             f"{entries} பதிவுகள் படிக்கப்பட்டன."]
    state = view.coverage.state if view.coverage else "unknown"
    parts.append({
        "sufficient":   "உங்களுக்குத் தேவையான வருடங்களை இந்தச் சான்றிதழ் "
                        "முழுமையாகக் காட்டுகிறது.",
        "insufficient": "உங்களுக்குத் தேவையான எல்லா வருடங்களையும் இந்தச் "
                        "சான்றிதழ் காட்டவில்லை — இன்னொரு சான்றிதழ் தேவைப்படும்.",
        "unknown":      "இந்தச் சான்றிதழ் எந்த வருடங்களைக் காட்டுகிறது என்று "
                        "படிக்க முடியவில்லை.",
    }[state])
    n = len(open_runs)
    if n:
        parts.append(f"{n} விஷயங்கள் இன்னும் உங்கள் கவனத்துக்குக் "
                     "காத்திருக்கின்றன.")
    parts.append("இப்போது கையெழுத்திடத் தயார்." if ready
                 else "இன்னும் கையெழுத்திடத் தயார் இல்லை.")
    return " ".join(parts)


def _as_sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "!", "?")) else text + "."
