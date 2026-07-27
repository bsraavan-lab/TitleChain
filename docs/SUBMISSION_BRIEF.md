# Buildathon submission brief

Answers for the "What did you build, and why?" form. Each field has a 2,000-character
limit; all of these fit with room to spare. Sources: [PRD.md](PRD.md),
[PROBLEM_AND_VALUE.md](PROBLEM_AND_VALUE.md), [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md).

---

## Project name

TitleChain

## Who are we building for?

A property advocate in Coimbatore. Call her Meena. She takes 8 to 15 title scrutiny
files a month, mostly for banks deciding whether to lend against a property. Every file
comes with a scanned Encumbrance Certificate: a dense Tamil table, 3 to 40 pages, one
row per registered transaction on that plot. She reads it on paper with a highlighter,
sketches the ownership chain on the file cover, and signs an opinion the bank will lend
crores against.

Her worry at the moment of signing isn't "did I misread row 23." It's "could this
certificate even answer the question I was asked." The certificate only shows a date
range someone guessed when ordering it, and nothing on the page tells her when the
chain of ownership starts before that window. If she was wrong, she finds out five to
ten years later, at foreclosure, by legal notice.

## What are we building?

Meena uploads the scanned EC. About ninety seconds later she gets the ownership chain
assembled for her: who transferred what to whom and in what order, which mortgages are
still alive, and where the chain breaks.

Then the part nothing else computes. Every entry in an EC carries a "previous document"
pointer, and those pointers often lead to years outside the window that was purchased.
TitleChain follows each pointer and says plainly which ones the evidence in hand cannot
reach. That single check tells her whether the certificate can support the opinion she
is about to sign.

Every finding is clickable back to a cropped image of the exact table cell it came
from, so the tool never asserts anything the page can't back up. And when the window
falls short, it drafts the replacement EC order for her (right sub-registrar office,
village, survey numbers, computed date range) so bad news comes with a same-day fix
instead of a blown deadline.

## Why would they use this over what they do today?

Today the safety system is paper and attention. Row 5 gets sharp attention; the
cancelled mortgage is in row 40. Services like Landeed made the certificate faster to
obtain, which turned out not to help much: she gets the same unread table, sooner. OCR
plus translation fails on its own terms, since the certificate is a picture of a table,
the meaning lives in which column a number sits in, and legal Tamil deed types collapse
into the same English word. But the deeper problem is that the answer she needs is not
written on any page. "Does this window cover the chain" is a computation over what the
document omits, and omissions have no text to translate.

Of five real certificates we pulled from public filings, three of the four we could
evaluate could not support the search they were ordered for. Nobody knew, because
nothing checks.

Where we're honest about the limits: TitleChain cannot see claims the registry never
recorded. It never opines on whether a title is good; a short window means the chain is
unverified, not that the title is bad. And v1 covers Tamil Nadu's computerised
post-1987 records only. Every finding cites its source crop, and the signature stays
human.
