# The profile: classic texts in USFM

USFM is the plain-text markup that Bible translations are exchanged in. It already carries the structure a reader
needs: paragraphs, verse lines, speakers, quotations, footnotes, and word-level data. This profile uses it for
texts that are not the Bible, so that a Platonic dialogue, a Hermetic hymn, a canto of Dante or a chapter of the
Gita can be read with the same structure, by the same tools.

Every file is valid USFM 3 (checked by [usfm-grammar](https://github.com/usfm-bible/tcdocs) in CI) and converts to
USJ (JSON) and USX (XML).

## A file

One file per edition of a work:

```
\id XXA symposium
\usfm 3.1
\ide UTF-8
\rem anagnosis work=symposium edition=loeb.eng lang=en
\rem source Perseus Digital Library (https://www.perseus.tufts.edu/), CC BY-SA 4.0; Plato, Symposium
\rem rights Translation public domain in the US; encoding CC BY-SA 4.0
\h Symposium
\toc1 Symposium
\mt1 Symposium
\c 1
\p
\v 1 \vp 172a\vp* \zsp Ap.|who="Apollodorus"\zsp* I believe I have got the story you inquire of pretty well by heart.
```

- `\id` takes an extra-book code (`XXA`) and the work's id.
- `\rem anagnosis` names the work, the edition and its language (ISO 639). `\rem source` gives provenance;
  `\rem rights` the licence. `\rem note` lines say what in the file is editorial.
- `\c` is the work's unit (a book of the Republic, a canto, a treatise), with `\cp` its printed label (`\cp VII`).
- `\v` numbers sections in order; `\vp` is the **printed reference** that scholarship cites: Stephanus `514a`, a
  canto's line `13`, a chapter of the Tao `42`. Editions of one work share these references, so a translation and
  its original align section by section without further work.

## Markers

| What | Marker |
|---|---|
| Paragraph | `\p` |
| Verse, a line each; stanza break (Dante's tercets) | `\q1 \v N \vp N\vp* …`, `\b` |
| A line break within a section | `\q1`, or `\qm1` within quoted verse |
| A speaker's label in the text (Plato's "SOC.", the Gita's "Arjuna said:") | `\zsp SOC.\|who="Socrates"\zsp*` |
| A speech in verse, from line to line (Dante's “…”) | `\zsay-s \|who="Virgil"\*` … `\zsay-e\*` |
| Verse or a hymn set off within prose (Homer in Plato; the Hermetic hymns) | `\zqm-s\*` … `\zqm-e\*`, lines as `\qm1` |
| A quotation | `\qt …\qt*` |
| A word left in its own language | `\tl …\tl*` |
| The edition's own note (Loeb's, Besant's, Wang Bi's commentary) | `\f + \fr 174b \ft …\f*` |
| A word of the original, with its lemma and parsing | `\w ἔρωτα\|lemma="ἔρως" x-morph="n-s---ma-"\w*` |

A character marker inside another is written with a plus (`\qt “\+w ναί|…\+w*”\qt*`), as USFM requires.
`x-morph` is the Perseus treebank's nine positions: part of speech, person, number, tense, mood, voice, gender,
case, degree.

## Invariants (checked in CI)

1. **The words are the edition's.** Markers add structure; they never change the text. Corrections to a source
   (OCR slips, transcription errors) are recorded where the files are made, each with its reason.
2. **Lossless.** Every file reads back into sections (text plus marks) that write out as exactly the same file
   (`tools/usfm_profile.py`, `read` and `write`).
3. Every printed reference is unique within its unit.
4. Every file names its source and its rights.
5. Every file parses with usfm-grammar and converts to USJ.
