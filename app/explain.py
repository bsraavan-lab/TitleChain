"""What an entry means, said plainly — the script behind the speaker button.

No model writes these sentences. Every clause is a template filled from the same
typed objects the checklist and the report render, and the deed-type opener is
keyed on derive.nature_kind() — the SAME classifier the rulebook runs — so the
voice can never call something a lease that R2 is treating as a mortgage. A
wrong simplification of a legal instrument is a liability, not a UX bug, which
is why the one place an LLM could have gone here is the one place it isn't.

Three languages, one structure. The Tamil and Hindi are spoken-register and
code-switch the way an advocate does across the desk — document numbers, dates
and the odd English legal term stay as written, because that is how they are
said aloud (bulbul's preprocessing reads them out). Findings are spoken from
per-rule templates where we have one, and in the rulebook's own English
sentence where we don't: an honest code-switch beats a guessed translation.
Both non-English registers await native-speaker review before a public demo.

R4 never appears in the flags section: the parents sentence IS the R4 content,
composed from the same edges, and hearing "it points back to 4451/2005, which is
not here" twice in one breath teaches the ear to skim — the exact failure
runs_grouped exists to prevent on the checklist.
"""

from __future__ import annotations

from .derive import nature_kind
from .models import DerivedView, Entry, RuleRun, OUTCOME_ORDER

LANGS = ("en", "ta", "hi")

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

_KIND_HI: dict[str | None, str] = {
    "transfer":     "यह प्रविष्टि संपत्ति का मालिकाना हक़ बदलने का रिकॉर्ड है — "
                    "{nature}। {ex} ने यह संपत्ति {cl} को दी है।",
    "encumbrance":  "यह एक गिरवी की प्रविष्टि है: {ex} ने यह संपत्ति {cl} के "
                    "पास क़र्ज़ की ज़मानत के तौर पर रखी है।",
    "discharge":    "यह एक रिलीज़ की प्रविष्टि है: इसमें संपत्ति पर चल रहा एक "
                    "पुराना क़र्ज़ बंद होने का रिकॉर्ड है।",
    "lease":        "यह एक पट्टे की प्रविष्टि है: {ex} ने यह संपत्ति {cl} को "
                    "किराये पर दी है।",
    "cancellation": "यह प्रविष्टि एक पुराना दस्तावेज़ रद्द करती है — उस "
                    "दस्तावेज़ में जो लिखा था, वह अब मान्य नहीं है।",
    None:           "यह प्रविष्टि किस तरह का दस्तावेज़ है, हम पक्के तौर पर नहीं "
                    "कह सके — कृपया इसे पन्ने पर ख़ुद पढ़ लें।",
}

# rule_id → per-language template for a spoken finding. {subject} is the run's
# own subject (a document number, mostly), which is language-neutral. Only the
# rules that fire per-entry today; anything else falls back to the English
# message.
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

_RULE_HI: dict[str, str] = {
    "R1":  "दस्तावेज़ {subject} बाद में रद्द कर दिया गया है — यह अब मालिकाना "
           "हक़ साबित नहीं करता।",
    "R2":  "इस गिरवी ({subject}) के बंद होने का कोई रिकॉर्ड नहीं है — संपत्ति "
           "पर यह क़र्ज़ अब भी हो सकता है।",
    "R9":  "इस प्रविष्टि के कुछ ख़ाने हम पढ़ नहीं सके — पन्ने पर सीधे देख लें।",
    "R10": "प्रमाणपत्र जितनी प्रविष्टियाँ बताता है और हमने जितनी पढ़ीं, वे "
           "मेल नहीं खातीं।",
}

_RULES = {"ta": _RULE_TA, "hi": _RULE_HI}


def _names(parties, lang: str) -> str:
    """Two names aloud, a count for the rest. Native script in BOTH languages:
    a name has one true form and it is the one on the page."""
    names = [p.name_native for p in parties if p.name_native]
    if not names:
        return {"en": "—", "ta": "பெயர் படிக்கப்படவில்லை",
                "hi": "नाम पढ़ा नहीं जा सका"}[lang]
    if len(names) <= 2:
        return {"en": " and ", "ta": " மற்றும் ", "hi": " और "}[lang].join(names)
    more = len(names) - 2
    if lang == "en":
        return f"{names[0]}, {names[1]} and {more} other{'s' if more > 1 else ''}"
    if lang == "hi":
        return f"{names[0]}, {names[1]} और {more} अन्य"
    return f"{names[0]}, {names[1]} மற்றும் இன்னும் {more} பேர்"


def _open_runs_for(entry: Entry, view: DerivedView) -> list[RuleRun]:
    rank = {o: i for i, o in enumerate(OUTCOME_ORDER)}
    mine = [r for r in view.runs
            if r.is_open and r.rule_id != "R4"
            and entry.db_id in r.evidence_entry_ids]
    return sorted(mine, key=lambda r: (rank[r.outcome], r.rule_id, r.key))


def _flag_sentence(run: RuleRun, lang: str) -> str:
    template = _RULES.get(lang, {}).get(run.rule_id)
    if template:
        return template.format(subject=run.subject)
    return run.message if run.message.endswith(".") else run.message + "."


def entry_script(entry: Entry, view: DerivedView, lang: str = "en") -> str:
    """The whole explanation, as one piece of text. Deterministic: same case,
    same words — which is also what lets speak.py cache the audio by content."""
    lang = lang if lang in LANGS else "en"
    parts: list[str] = []

    doc = entry.doc_no or {"en": "no readable number",
                           "ta": "எண் படிக்கப்படவில்லை",
                           "hi": "नंबर पढ़ा नहीं जा सका"}[lang]
    when = entry.date_registration or entry.date_execution
    if lang == "en":
        opener = f"Entry {entry.sr_no} — document {doc}"
        opener += f", registered on {when}." if when else ". We could not read its date."
    elif lang == "hi":
        opener = f"प्रविष्टि {entry.sr_no} — दस्तावेज़ {doc}"
        opener += (f", {when} को पंजीकृत हुआ।" if when
                   else "। इसकी तारीख़ पढ़ी नहीं जा सकी।")
    else:
        opener = f"பதிவு {entry.sr_no} — ஆவணம் {doc}"
        opener += (f", {when} அன்று பதிவு செய்யப்பட்டது."
                   if when else ". இதன் தேதியைப் படிக்க முடியவில்லை.")
    parts.append(opener)

    kind = nature_kind(entry.nature)
    table = {"en": _KIND_EN, "ta": _KIND_TA, "hi": _KIND_HI}[lang]
    parts.append(table[kind].format(
        nature=entry.nature or "",
        ex=_names(entry.executants, lang), cl=_names(entry.claimants, lang)))

    value = entry.market_value or entry.consideration_value
    if value and value.strip() not in ("-", "—"):
        parts.append({"en": f"The value on the page is {value}.",
                      "ta": f"பக்கத்தில் உள்ள மதிப்பு: {value}.",
                      "hi": f"पन्ने पर लिखी क़ीमत: {value}।"}[lang])

    parts.append(_parents_sentence(entry, view, lang))

    flags = _open_runs_for(entry, view)[:MAX_FLAGS]
    if flags:
        parts.append({"en": "Worth your attention:",
                      "ta": "கவனிக்க வேண்டியது:",
                      "hi": "ध्यान देने लायक़ बातें:"}[lang])
        parts.extend(_flag_sentence(r, lang) for r in flags)
    else:
        parts.append({
            "en": "Nothing else on this case is flagged against this entry.",
            "ta": "இந்தப் பதிவின் மேல் வேறு எந்தப் பிரச்சனையும் இந்த "
                  "கேஸில் குறிக்கப்படவில்லை.",
            "hi": "इस प्रविष्टि पर इस केस में और कोई समस्या दर्ज नहीं है।",
        }[lang])

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
    extra = len(docs) - 3
    spoken = ", ".join(docs[:3]) + ("" if extra <= 0 else {
        "en": f" and {extra} more", "ta": f" இன்னும் {extra}",
        "hi": f" और {extra} अन्य"}[lang])
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

    if lang == "hi":
        n = len(docs)
        head = (f"यह दस्तावेज़ {n} पुराने दस्तावेज़{'ों का' if n > 1 else ' का'} "
                f"हवाला देता है — {spoken}।")
        if missing == 0:
            return head + " वे सभी इस केस में मौजूद हैं।"
        if missing == n:
            return (head + " उनमें से कोई भी इस केस में नहीं है — उनके अंदर "
                    "क्या लिखा है, यह यहाँ किसी ने नहीं पढ़ा।")
        return (head + f" इनमें से {missing} इस केस में नहीं "
                f"{'हैं' if missing > 1 else 'है'} — उन्हें यहाँ किसी ने "
                "नहीं पढ़ा।")

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
    whether it can be signed. The Tamil and Hindi are composed from the
    derivation's own numbers and states rather than translating the English
    verdict, because the verdict is a case-specific sentence and a guessed
    translation of a legal conclusion is the one thing this module refuses to
    produce."""
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

    if lang == "hi":
        entries = sum(len(d.entries) for d in view.docs)
        parts = [f"इस केस की स्थिति यह है। {len(view.docs)} प्रमाणपत्र, "
                 f"{entries} प्रविष्टियाँ पढ़ी गईं।"]
        state = view.coverage.state if view.coverage else "unknown"
        parts.append({
            "sufficient":   "आपको जिन वर्षों की जाँच चाहिए, यह प्रमाणपत्र उन्हें "
                            "पूरी तरह दिखाता है।",
            "insufficient": "आपको जिन वर्षों की जाँच चाहिए, यह प्रमाणपत्र उन "
                            "सभी को नहीं दिखाता — एक और प्रमाणपत्र लगेगा।",
            "unknown":      "यह प्रमाणपत्र कौन से वर्ष दिखाता है, यह पढ़ा नहीं "
                            "जा सका।",
        }[state])
        n = len(open_runs)
        if n:
            parts.append(f"{n} बातें अभी भी आपके ध्यान का इंतज़ार कर रही हैं।")
        parts.append("अब दस्तख़त के लिए तैयार है।" if ready
                     else "अभी दस्तख़त के लिए तैयार नहीं है।")
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
