# Anagnosis texts

Classic texts in plain, structured, open USFM: each with its speakers, verse, quotations and its edition's own
notes marked, and with its original language beside it. The Greek of Plato and Plotinus has every word's lemma and
parsing; Plotinus's quotations of Plato carry their source (a CTS URN); and every file has a CTS URN of its own.

These are the open editions behind [Anagnosis](https://anagnosis.sh), a reader of scripture and the
traditions around it. They are published here so that anyone can read them, build on them or correct them.

## Editions

| Text | Edition | Language | Files | Sections | Folder | Licence |
|---|---|---|---|---|---|---|
| Plato | Loeb (1914–35) | English | 36 | 8,548 | [plato-loeb](texts/plato-loeb) | CC BY-SA 4.0 |
| Plato | Greek (Burnet) | Greek | 36 | 8,552 | [plato-burnet](texts/plato-burnet) | CC BY-SA 4.0 |
| Bhagavad Gita | Besant (1922) | English | 1 | 701 | [gita-besant](texts/gita-besant) | Public domain text; markup CC0 1.0 |
| Bhagavad Gita | Sanskrit | Sanskrit | 1 | 701 | [gita-sanskrit](texts/gita-sanskrit) | Public domain text; markup CC0 1.0 |
| Dante, Divine Comedy | Longfellow (1867) | English | 3 | 14,233 | [dante-longfellow](texts/dante-longfellow) | Public domain text; markup CC0 1.0 |
| Dante, Divine Comedy | Italian | Italian | 3 | 14,233 | [dante-italian](texts/dante-italian) | Public domain text; markup CC0 1.0 |
| Corpus Hermeticum and Asclepius | Mead (1906) | English | 2 | 275 | [hermetica-mead](texts/hermetica-mead) | Public domain text; markup CC0 1.0 |
| Tao Te Ching | Legge (1891) | English | 1 | 81 | [chinese-legge](texts/chinese-legge) | Public domain text; markup CC0 1.0 |
| Tao Te Ching | Chinese (Wang Bi) | Classical Chinese | 1 | 81 | [chinese-wangbi](texts/chinese-wangbi) | Public domain text; markup CC0 1.0 |
| Plotinus, Enneads | MacKenna | English | 1 | 650 | [greek-plotinus-mackenna](texts/greek-plotinus-mackenna) | Public domain in the US; markup CC0 1.0 |
| Plotinus, Enneads | Greek (Volkmann) | Greek | 1 | 653 | [greek-plotinus-volkmann](texts/greek-plotinus-volkmann) | CC BY-SA 4.0 |

## Why USFM

USFM is the plain-text format Bible translations are exchanged in. It is readable and editable by hand, its changes
diff cleanly, and it already has markup for speakers, verse lines, quotations, notes and word-level data. It
converts to JSON (USJ) and XML (USX). Using it for other texts means one parser and one reader for all of them.
[PROFILE.md](PROFILE.md) describes how it is used here.

## Using the files

- **Python**: `tools/usfm_profile.py` reads a file into sections (`read`), each its text and its marks
  (speaker, speech, quotation, note…) as offsets into that text, and writes them back (`write`).
- **Words**: Plato's Greek words, each with its lemma and parsing, are in `texts/plato-burnet/words/*.tsv`, keyed
  by section and word number, beside the text rather than in it.
- **JSON**: every push builds USJ for every file (the `usj` artifact of the `check` workflow), or run
  `npm install && node tools/validate.mjs --usj out/`.
- Any USFM parser (usfm-grammar, usfm-js) reads the files; the profile's own markers (`\z…`: speakers, speeches,
  quoted verse) mean something only to readers that know the profile. Every file is the extra-book `XXA`, so in
  Paratext each work would be a project of its own.

## Checks

On every push, `tools/check.py` confirms each file is lossless (it reads back into exactly the same file), names its
source and rights, has unique references, and that every word in a sidecar is the word at that place; `tools/validate.mjs` parses each with
[usfm-grammar](https://www.npmjs.com/package/usfm-grammar) and converts it to USJ.

## What is editorial

The words are the editions'. Where a source was wrong (an OCR slip, a footnote the scan ran into the text), the
correction is recorded with its reason where these files are made. Marked as editorial in each file's
`\rem note`: who speaks each of Dante's speeches, which of Mead's passages are hymns, and the Greek words'
lemmas and parsing (automatic, from GLAUx: lemmas about 98.8% right, parsing about 97%).

Corrections are welcome as issues or pull requests.

## Licences

See [LICENSE.md](LICENSE.md). The Plato files are CC BY-SA 4.0, after Perseus and GLAUx. The other texts are in
the public domain, and the markup added to them is CC0.
