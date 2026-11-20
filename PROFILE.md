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
\rem anagnosis work=symposium edition=loeb.eng lang=en urn=urn:cts:greekLit:tlg0059.tlg011.perseus-eng2 cite=vp
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
- `\rem anagnosis` names the work, the edition and its language (ISO 639), and the edition's **CTS URN** with how a
  section is cited under it. Plato's are the Perseus URNs, so these files address the same passages as Perseus,
  Scaife and GLAUx. The other texts have no CTS namespace; their URNs are minted in the same shape under
  `urn:cts:anagnosis:` (`urn:cts:anagnosis:dante.inferno.longfellow-eng`).
- A section's URN is the file's URN, a colon, and its citation: `cite=vp` the printed reference
  (`…tlg011.perseus-eng2:172a`), `cite=c.vp` the unit's number and the reference (`…tlg030.perseus-eng2:7.514a`, a
  canto's line `…inferno.longfellow-eng:5.121`), `cite=cp.vp` the unit's printed label and the reference
  (`…hermetica.ch.mead-eng:XIII.17`).
- `\rem source` gives provenance; `\rem rights` the licence; `\rem note` lines say what in the file is editorial.
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
| A speech, from its first word to its last (Plato's, from Perseus's `<said>`; Dante's “…”) | `\zsay-s \|who="Socrates"\*` … `\zsay-e\*` |
| Verse or a hymn set off within prose (Homer in Plato; the Hermetic hymns) | `\zqm-s\*` … `\zqm-e\*`, lines as `\qm1` |
| A quotation; with its source, a CTS URN (Plotinus quoting Plato) | `\qt …\qt*`, `\qt …\qt*\rq urn:cts:greekLit:tlg0059.tlg012.perseus-grc2:246b\rq*` |
| A word left in its own language | `\tl …\tl*` |
| The edition's own note (Loeb's, Besant's, Wang Bi's commentary) | `\f + \fr 174b \ft …\f*` |

A character marker inside another is written with a plus (`\+tl`), as USFM requires.

A speech crossing a section is closed at the section's end and opened again in the next, so every section stands
alone; its speaker is the same name in a translation and its original (Plato's Greek speeches are named as the
Loeb's are). Plato and Dante have speeches; Mead and the Gita have their printed labels only.

## Words of an original: beside the text, not in it

The original's word-level data is kept out of the USFM, in a sidecar per work (`texts/plato-burnet/words/<work>.tsv`,
`texts/greek-plotinus-volkmann/words/enneads.tsv`),
so the text stays clean to read, to correct, and to diff:

```
# unit	ref	n	form	lemma	morph
	172a	1	δοκῶ	δοκέω	v1spia---
```

`unit` and `ref` are the section's `\cp` and `\vp`; `n` counts the section's words of the original from 0 (Greek
letters with their accents, and a final elision mark: `tools/usfm_profile.py`, `WORD`); `morph` is the Perseus
treebank's nine positions (part of speech, person, number, tense, mood, voice, gender, case, degree). The check
confirms every row's word is the word at that place. Merged, a row is USFM's `\w ἔρωτα|lemma="ἔρως"
x-morph="n-s---ma-"\w*`.

## Invariants (checked in CI)

1. **The words are the edition's.** Markers add structure; they never change the text. Corrections to a source
   (OCR slips, transcription errors) are recorded where the files are made, each with its reason.
2. **Lossless.** Every file reads back into sections (text plus marks) that write out as exactly the same file
   (`tools/usfm_profile.py`, `read` and `write`).
3. Every printed reference is unique within its unit.
4. Every file names its source and its rights.
5. Every file parses with usfm-grammar and converts to USJ.
6. No speaker's label, quotation or word runs across a paragraph; every sidecar row names the word that is there.

## What generic USFM tools will see

These are USFM 3 files, but the profile is its own: the `\z…` markers (speakers, speeches, quoted verse) are
meaningful only to readers that know the profile, and a generic tool will pass over them; `\v` is a running
number, and the reference to cite is `\vp`. Every file uses the extra-book code `XXA`, so a Paratext project holds
one work at a time.
