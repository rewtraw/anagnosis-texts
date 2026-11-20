"""The USFM profile for classic texts (PROFILE.md; in Anagnosis, docs/text-standard.md): write a work's sections, with their marks, as USFM, and read
them back. Converters produce (text, marks) per section; write() makes the USFM file; read() must give back exactly
the same text and marks, or the converter fails (a lossless round trip is the profile's first invariant).

A section is its printed reference ("172a"), its text (the edition's words, paragraphs "\\n\\n", lines "\\n"), and
its marks, each [kind, start, end, data] over the text:
  sp  a speaker's label in the text ("Ap."), data the speaker ("Apollodorus")
  q   a quotation from another text, inline, data its source   \\qt …\\qt*\\rq urn\\rq*
  qm  verse quoted within prose, a block of lines              \\qm1 per line
  tl  a word left in its own language                          \\tl …\\tl*
  f   a note at a point (start == end), data its text          \\f + \\fr ref \\ft …\\f*
  ref a reference the edition prints, data its target (USFM "SNG 2:2", or a URN)   \\jmp …|link-href=""\\jmp*
  w   a word of the original, data its lemma and parsing        \\w form|lemma="" x-morph=""\\w*
  say a speech in verse (Dante's), data the speaker              \\zsay-s |who=""\\* … \\zsay-e\\*
"""
import re

KINDS = ("sp", "q", "qm", "tl", "f", "say", "w", "ref")
CHAR = {"q": ("\\qt ", "\\qt*"), "tl": ("\\tl ", "\\tl*")}


def note_text(text):
    """A note as USFM can carry it: one line, and no backslash or bar (which open markers and attributes); a bar that
    divides verse lines in a quotation ("…ἀεικέα | ζώῃ…") becomes the slash that also does."""
    return re.sub(r"\s+", " ", text).replace("\\", "/").replace("|", "/").strip()


def section_usfm(ref, text, marks):
    """One section's USFM body (everything after its \\v … \\vp …\\vp*)."""
    opens, closes, points = {}, {}, {}
    # Spans nest: of two opening at one point the longer opens first (and so closes last). A character span inside
    # another (a word in a quotation) is written with a plus, as USFM asks: \\+w … \\+w*.
    spans = [(s, e) for k, s, e, *_ in marks if k in ("q", "tl", "sp")]
    def plus(kind, start, end):
        return "+" if any(s <= start and end <= e and (s, e) != (start, end) for s, e in spans) or \
            (kind == "w" and (start, end) in spans) else ""
    for kind, start, end, *data in sorted(marks, key=lambda m: (m[1], -m[2])):
        if kind == "f":
            points.setdefault(start, []).append(f"\\f + \\fr {ref} \\ft {note_text(data[0])}\\f*")
        elif kind == "sp":
            opens.setdefault(start, []).append("\\zsp ")
            closes.setdefault(end, []).insert(0, f'|who="{data[0]}"\\zsp*')
        elif kind == "qm":  # verse quoted in prose: milestones bound it (it may begin in an earlier section)
            opens.setdefault(start, []).append("\\zqm-s\\*")
            closes.setdefault(end, []).insert(0, "\\zqm-e\\*")
        elif kind == "say":  # a speech: milestones, since it runs on from line to line
            opens.setdefault(start, []).append(f'\\zsay-s |who="{data[0]}"\\*')
            closes.setdefault(end, []).insert(0, "\\zsay-e\\*")
        elif kind == "ref":  # a reference the edition prints, "(S.S. 2, 2)", linked to what it names
            p = plus(kind, start, end)
            opens.setdefault(start, []).append(f"\\{p}jmp ")
            closes.setdefault(end, []).insert(0, f'|link-href="{data[0]}"\\{p}jmp*')
        elif kind == "w":  # a word of the original: its lemma and parsing
            p = plus(kind, start, end)
            opens.setdefault(start, []).append(f"\\{p}w ")
            closes.setdefault(end, []).insert(0, f'|lemma="{data[0]}" x-morph="{data[1]}"\\{p}w*')
        elif kind in CHAR:
            p = plus(kind, start, end)
            opens.setdefault(start, []).append(CHAR[kind][0].replace("\\", "\\" + p))
            # A quotation's source, where known: \\rq after it (a CTS URN: "urn:cts:greekLit:tlg0059.tlg031.perseus-grc2:37d").
            source = f"\\rq {data[0]}\\rq*" if kind == "q" and data and data[0] else ""
            closes.setdefault(end, []).insert(0, CHAR[kind][1].replace("\\", "\\" + p) + source)
    verse = [(s, e) for k, s, e, *_ in marks if k == "qm"]
    in_verse = lambda i: any(s <= i < e for s, e in verse)
    out, i = [], 0
    while i <= len(text):
        out += closes.get(i, [])
        out += points.get(i, [])
        out += opens.get(i, [])
        if i == len(text):
            break
        if text.startswith("\n\n", i):
            out.append("\n\\p "); i += 2; continue
        if text[i] == "\n":
            out.append("\n\\qm1 " if in_verse(i) else "\n\\q1 "); i += 1; continue
        out.append(text[i]); i += 1
    return "".join(out)


_TOKEN = re.compile(r'\\zsay-s \|who="(?P<say>[^"]*)"\\\*|\\zsay-e\\\*|\\zqm-s\\\*|\\zqm-e\\\*|\n\\p |\n\\qm1 |\n\\q1 '
                    r'|\\\+?qt\*\\rq (?P<rq>[^\\]+)\\rq\*|\\\+?qt\*|\\\+?qt |\\\+?tl\*|\\\+?tl |\\zsp |\|who="(?P<sp>[^"]*)"\\zsp\*|\\\+?w |\|lemma="(?P<lemma>[^"]*)" x-morph="(?P<morph>[^"]*)"\\\+?w\*'
                    r'|\\\+?jmp |\|link-href="(?P<href>[^"]*)"\\\+?jmp\*'
                    r'|\\f \+ \\fr [^\\]*\\ft (?P<note>.*?)\\f\*', re.S)
ORDER = lambda m: (m[1], m[2], m[0])


def read_section(body):
    """The inverse of section_usfm: (text, marks)."""
    text, marks, stack, verse_start, at, pos = [], [], [], None, 0, 0
    def close(kind):
        entry = next(x for x in reversed(stack) if x[0] == kind)
        stack.remove(entry)
        return entry
    for m in _TOKEN.finditer(body):
        piece = body[pos:m.start()]
        text.append(piece); at += len(piece); pos = m.end()
        tok = m.group(0).replace("\\+", "\\")
        if m.group("say") is not None:
            stack.append(("say", at, m.group("say")))
        elif tok == "\\zsay-e\\*":
            _, start, who = close("say")
            marks.append(["say", start, at, who])
        elif tok == "\\zqm-s\\*":
            verse_start = at
        elif tok == "\\zqm-e\\*":
            marks.append(["qm", verse_start, at]); verse_start = None
        elif tok == "\n\\p ":
            text.append("\n\n"); at += 2
        elif tok in ("\n\\qm1 ", "\n\\q1 "):
            text.append("\n"); at += 1
        elif tok in ("\\qt ", "\\tl ", "\\zsp ", "\\w ", "\\jmp "):
            stack.append((tok, at))
        elif m.group("rq") is not None:
            marks.append(["q", close("\\qt ")[1], at, m.group("rq")])
        elif tok in ("\\qt*", "\\tl*"):
            kind = "q" if tok == "\\qt*" else "tl"
            marks.append([kind, close(CHAR[kind][0])[1], at])
        elif m.group("sp") is not None:
            marks.append(["sp", close("\\zsp ")[1], at, m.group("sp")])
        elif m.group("href") is not None:
            marks.append(["ref", close("\\jmp ")[1], at, m.group("href")])
        elif m.group("lemma") is not None:
            marks.append(["w", close("\\w ")[1], at, m.group("lemma"), m.group("morph")])
        elif m.group("note") is not None:
            marks.append(["f", at, at, m.group("note")])
    text.append(body[pos:])
    return "".join(text), sorted(marks, key=ORDER)


def write(meta, units):
    """A work's USFM file. meta: work, edition, lang, title, source, rights (and stanza, for verse). units: [(label or "", [(ref, text, marks)])]."""
    lines = [f"\\id XXA {meta['work']}", "\\usfm 3.1", "\\ide UTF-8",
             f"\\rem anagnosis work={meta['work']} edition={meta['edition']} lang={meta['lang']}"
             + (f" urn={meta['urn']} cite={meta.get('cite', 'vp')}" if meta.get("urn") else ""),
             f"\\rem source {meta['source']}", f"\\rem rights {meta['rights']}",
             *(f"\\rem note {n.replace(chr(92), '')}" for n in meta.get("notes", ())),  # a backslash would open a marker
             f"\\h {meta['title']}", f"\\toc1 {meta['title']}", f"\\mt1 {meta['title']}"]
    for c, (label, sections) in enumerate(units, 1):
        lines.append(f"\\c {c}" + (f"\n\\cp {label}" if label else ""))
        if meta.get("stanza"):  # verse: a line each (\\q1), a blank line (\\b) between stanzas of `stanza` lines
            for v, (ref, text, marks) in enumerate(sections, 1):
                if v > 1 and (v - 1) % meta["stanza"] == 0:
                    lines.append("\\b")
                lines.append(f"\\q1 \\v {v} \\vp {ref}\\vp* " + section_usfm(ref, text, marks))
            continue
        lines.append("\\p")
        for v, (ref, text, marks) in enumerate(sections, 1):
            lines.append(f"\\v {v} \\vp {ref}\\vp* " + section_usfm(ref, text, marks))
    return "\n".join(lines) + "\n"


def read(usfm):
    """{(unit label, ref): (text, marks)} from a file written by write()."""
    out, label = {}, ""
    for block in re.split(r"\n(?=\\c \d+)", usfm):
        m = re.match(r"\\c \d+(?:\n\\cp (\S+))?", block)
        if m:
            label = m.group(1) or ""
        for v in re.finditer(r"\n(?:\\q1 )?\\v \d+ \\vp ([^\\]+)\\vp\* (.*?)(?=\n(?:\\b\n)?(?:\\q1 )?\\v \d+ |\n\\c \d+|\Z)", block, re.S):
            out[(label, v.group(1))] = read_section(v.group(2).rstrip("\n"))  # texts never end in a newline
    return out


def place(rich, plain, is_mark):
    """Where the mark characters in `rich` fall in `plain`: rich is plain with mark characters added, its spacing perhaps
    differing (a mark taken out of "word ∗ word" leaves two spaces where the plain text has one). [(char, offset)], or
    None if the words differ."""
    out, j = [], 0
    for ch in rich:
        if is_mark(ch):
            out.append((ch, j))
        elif j < len(plain) and ch == plain[j]:
            j += 1
        elif not ch.isspace():
            while j < len(plain) and plain[j].isspace():
                j += 1
            if j < len(plain) and ch == plain[j]:
                j += 1
            else:
                return None
    if plain[j:].strip():
        return None
    return [(ch, min(at, len(plain))) for ch, at in out]


def write_checked(path, meta, units):
    """Write a work's USFM file (see write) and read it back: the same words and marks, or the converter stops."""
    text = write(meta, units)
    back = read(text)
    for label, sections in units:
        for ref, t, m in sections:
            if back.get((label, ref)) != (t, sorted([list(x) for x in m], key=ORDER)):
                raise SystemExit(f"USFM round trip failed: {meta['work']} {label} {ref}\n{back.get((label, ref))}\n{(t, m)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def meta_of(usfm):
    """A file's header, as write() takes it: work, edition, lang, title, source, rights, notes, and stanza for verse."""
    head = usfm.split("\n\\c ", 1)[0]
    rem = re.search(r"^\\rem anagnosis work=(\S+) edition=(\S+) lang=(\S+)(?: urn=(\S+) cite=(\S+))?$", head, re.M)
    meta = {"work": rem[1], "edition": rem[2], "lang": rem[3], **({"urn": rem[4], "cite": rem[5]} if rem[4] else {}),
            "source": re.search(r"^\\rem source (.*)$", head, re.M)[1], "rights": re.search(r"^\\rem rights (.*)$", head, re.M)[1],
            "title": re.search(r"^\\h (.*)$", head, re.M)[1], "notes": re.findall(r"^\\rem note (.*)$", head, re.M)}
    if "\n\\b\n" in usfm:  # verse in stanzas: as many lines as stand before the first blank line
        first = usfm[usfm.index("\n\\c "):usfm.index("\n\\b\n")]
        meta["stanza"] = first.count("\n\\q1 \\v ")
    return meta


def check(usfm):
    """The profile's invariants for one file (docs/text-standard.md): what is wrong with it, or nothing.
    It names its source and rights; each printed reference is unique within its unit; and it reads back into
    sections that write out as exactly the same file (nothing lost between the text and its marks)."""
    problems = []
    try:
        meta = meta_of(usfm)
    except (TypeError, AttributeError):
        return ["the header lacks \\rem anagnosis, \\rem source, \\rem rights or \\h"]
    if not meta["rights"].strip() or not meta["source"].strip():
        problems.append("no source or no rights")
    if any("\\" in line[1:] for line in usfm.split("\n\\c ", 1)[0].splitlines() if line.startswith(("\\rem", "\\h", "\\toc", "\\mt"))):
        problems.append("a backslash inside a header line (it opens a marker)")
    units, seen = [], set()
    for block in re.split(r"\n(?=\\c \d+)", usfm)[1:]:
        label = (re.match(r"\\c \d+(?:\n\\cp (\S+))?", block)[1]) or ""
        sections = []
        for v in re.finditer(r"\n(?:\\q1 )?\\v \d+ \\vp ([^\\]+)\\vp\* (.*?)(?=\n(?:\\b\n)?(?:\\q1 )?\\v \d+ |\n\\c \d+|\Z)", block, re.S):
            if (label, v[1]) in seen:
                problems.append(f"{label} {v[1]} appears twice")
            seen.add((label, v[1]))
            text, marks = read_section(v[2].rstrip("\n"))
            if "|" in text or "\\" in text:
                problems.append(f"{label} {v[1]}: a bare | or \\ in the text (USFM's attribute separator, or a marker)")
            for kind, start, end, *_ in marks:  # a speaker's label, a quotation, a word: within one paragraph
                if kind in ("sp", "q", "tl", "w") and "\n\n" in text[start:end]:
                    problems.append(f"{label} {v[1]}: a {kind} span runs across a paragraph break")
            sections.append((v[1], text, marks))
        units.append((label, sections))
    if write(meta, units) != usfm:
        problems.append("does not read back into exactly the same file")
    return problems


# ---------------------------------------------------------------- word-level data, beside the text

# The words of an original, counted in a section's text in order: Greek letters with their accents, and an elision
# mark if one ends the word ("ταῦτʼ"). A sidecar file names each annotated word by its section and this index.
WORD = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F]+(?:[’'ʼ᾽](?![\u0370-\u03FF\u1F00-\u1FFF]))?")


def words_tsv(units):
    """A work's words with their lemma and parsing, as the sidecar beside its USFM (words/<work>.tsv): one row per
    word, `unit  ref  n  form  lemma  morph`, n counting WORD tokens in the section's text from 0. units: [(label,
    [(ref, text, marks)])], the word marks ["w", start, end, lemma, morph] among the marks."""
    rows = ["# unit\tref\tn\tform\tlemma\tmorph"]
    for label, sections in units:
        for ref, text, marks in sections:
            index = {(m.start(), m.end()): n for n, m in enumerate(WORD.finditer(text))}
            for k, a, b, *data in marks:
                if k == "w":
                    rows.append("\t".join([label, ref, str(index[(a, b)]), text[a:b], data[0], data[1]]))
    return "\n".join(rows) + "\n"


def check_words(usfm, tsv):
    """A sidecar against its text: every row names a section the file has, and the word it gives is the word there."""
    sections = {}
    label = ""
    for block in re.split(r"\n(?=\\c \d+)", usfm)[1:]:
        label = (re.match(r"\\c \d+(?:\n\\cp (\S+))?", block)[1]) or ""
        for v in re.finditer(r"\n(?:\\q1 )?\\v \d+ \\vp ([^\\]+)\\vp\* (.*?)(?=\n(?:\\b\n)?(?:\\q1 )?\\v \d+ |\n\\c \d+|\Z)", block, re.S):
            sections[(label, v[1])] = [m.group() for m in WORD.finditer(read_section(v[2].rstrip("\n"))[0])]
    problems = []
    for n, line in enumerate(tsv.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        unit, ref, i, form, lemma, morph = line.split("\t")
        words = sections.get((unit, ref))
        if words is None:
            problems.append(f"line {n}: no section {unit} {ref}".strip())
        elif int(i) >= len(words) or words[int(i)] != form:
            problems.append(f"line {n}: {unit} {ref} word {i} is not {form}")
    return problems


def speeches_from_labels(sections, starts=None, narration=None):
    """Speeches where an edition prints only its speakers' labels ("Arjuna said:", "Hermes."): each label's speech runs
    to the next label, across sections, and ends with them (a chapter, a tractate: pass one unit at a time).
    sections: [(ref, text, marks)] in order → the same, each with its say marks (one per section a speech crosses),
    any say marks it had replaced. starts: {section index: speaker} for a turn the edition prints no label for (the
    Gita's English at 6.33, where the Sanskrit has one): it begins at the section's start. narration: whether a
    paragraph is the narrator's (Mead's Asclepius: "Whom when Thrice-greatest heard, he grew distressed and said:"),
    which no speech includes."""
    labels = [(i, m[1], m[3]) for i, (_, _, marks) in enumerate(sections) for m in sorted(marks, key=ORDER) if m[0] == "sp"]
    labels = sorted(labels + [(i, 0, who) for i, who in (starts or {}).items()
                              if not any(j == i and a == 0 for j, a, _ in labels)])
    adds = {}
    for n, (i, a, who) in enumerate(labels):
        j, b = (labels[n + 1][0], labels[n + 1][1]) if n + 1 < len(labels) else (len(sections) - 1, None)
        for k in range(i, j + 1):
            text = sections[k][1]
            lo = a if k == i else 0
            hi = (b if b is not None and k == j else len(text))
            while hi > lo and text[hi - 1].isspace():
                hi -= 1
            if hi > lo:
                adds.setdefault(k, []).append(["say", lo, hi, who])
    if narration:
        for k, says in adds.items():
            text = sections[k][1]
            told = [(m.start(1), m.end(1)) for m in re.finditer(r"(?:^|\n\n)([^\n]+)", text) if narration(m.group(1))]
            if not told:
                continue
            cut = []
            for _, lo, hi, who in says:
                for a, b in told:  # the speech, less the narrator's paragraphs within it
                    if a < hi and b > lo:
                        if a > lo:
                            cut.append(["say", lo, a, who])
                        lo = b
                while lo < hi and text[lo].isspace():
                    lo += 1
                if hi > lo:
                    cut.append(["say", lo, hi, who])
            for m in cut:
                while m[2] > m[1] and text[m[2] - 1].isspace():
                    m[2] -= 1
            adds[k] = [m for m in cut if m[2] > m[1]]
    return [(ref, text, sorted([m for m in marks if m[0] != "say"] + adds.get(k, []), key=ORDER))
            for k, (ref, text, marks) in enumerate(sections)]
