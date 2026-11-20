"""The USFM profile for classic texts (PROFILE.md; in Anagnosis, docs/text-standard.md): write a work's sections, with their marks, as USFM, and read
them back. Converters produce (text, marks) per section; write() makes the USFM file; read() must give back exactly
the same text and marks, or the converter fails (a lossless round trip is the profile's first invariant).

A section is its printed reference ("172a"), its text (the edition's words, paragraphs "\\n\\n", lines "\\n"), and
its marks, each [kind, start, end, data] over the text:
  sp  a speaker's label in the text ("Ap."), data the speaker ("Apollodorus")
  q   a quotation from another text, inline                    \\qt …\\qt*
  qm  verse quoted within prose, a block of lines              \\qm1 per line
  tl  a word left in its own language                          \\tl …\\tl*
  f   a note at a point (start == end), data its text          \\f + \\fr ref \\ft …\\f*
  w   a word of the original, data its lemma and parsing        \\w form|lemma="" x-morph=""\\w*
  say a speech in verse (Dante's), data the speaker              \\zsay-s |who=""\\* … \\zsay-e\\*
"""
import re

KINDS = ("sp", "q", "qm", "tl", "f", "say", "w")
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
        elif kind == "w":  # a word of the original: its lemma and parsing
            p = plus(kind, start, end)
            opens.setdefault(start, []).append(f"\\{p}w ")
            closes.setdefault(end, []).insert(0, f'|lemma="{data[0]}" x-morph="{data[1]}"\\{p}w*')
        elif kind in CHAR:
            p = plus(kind, start, end)
            opens.setdefault(start, []).append(CHAR[kind][0].replace("\\", "\\" + p))
            closes.setdefault(end, []).insert(0, CHAR[kind][1].replace("\\", "\\" + p))
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
                    r'|\\\+?qt\*|\\\+?qt |\\\+?tl\*|\\\+?tl |\\zsp |\|who="(?P<sp>[^"]*)"\\zsp\*|\\\+?w |\|lemma="(?P<lemma>[^"]*)" x-morph="(?P<morph>[^"]*)"\\\+?w\*'
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
        elif tok in ("\\qt ", "\\tl ", "\\zsp ", "\\w "):
            stack.append((tok, at))
        elif tok in ("\\qt*", "\\tl*"):
            kind = "q" if tok == "\\qt*" else "tl"
            marks.append([kind, close(CHAR[kind][0])[1], at])
        elif m.group("sp") is not None:
            marks.append(["sp", close("\\zsp ")[1], at, m.group("sp")])
        elif m.group("lemma") is not None:
            marks.append(["w", close("\\w ")[1], at, m.group("lemma"), m.group("morph")])
        elif m.group("note") is not None:
            marks.append(["f", at, at, m.group("note")])
    text.append(body[pos:])
    return "".join(text), sorted(marks, key=ORDER)


def write(meta, units):
    """A work's USFM file. meta: work, edition, lang, title, source, rights (and stanza, for verse). units: [(label or "", [(ref, text, marks)])]."""
    lines = [f"\\id XXA {meta['work']}", "\\usfm 3.1", "\\ide UTF-8",
             f"\\rem anagnosis work={meta['work']} edition={meta['edition']} lang={meta['lang']}",
             f"\\rem source {meta['source']}", f"\\rem rights {meta['rights']}",
             *(f"\\rem note {n}" for n in meta.get("notes", ())),
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
    rem = re.search(r"^\\rem anagnosis work=(\S+) edition=(\S+) lang=(\S+)$", head, re.M)
    meta = {"work": rem[1], "edition": rem[2], "lang": rem[3],
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
    units, seen = [], set()
    for block in re.split(r"\n(?=\\c \d+)", usfm)[1:]:
        label = (re.match(r"\\c \d+(?:\n\\cp (\S+))?", block)[1]) or ""
        sections = []
        for v in re.finditer(r"\n(?:\\q1 )?\\v \d+ \\vp ([^\\]+)\\vp\* (.*?)(?=\n(?:\\b\n)?(?:\\q1 )?\\v \d+ |\n\\c \d+|\Z)", block, re.S):
            if (label, v[1]) in seen:
                problems.append(f"{label} {v[1]} appears twice")
            seen.add((label, v[1]))
            text, marks = read_section(v[2].rstrip("\n"))
            for kind, start, end, *_ in marks:  # a speaker's label, a quotation, a word: within one paragraph
                if kind in ("sp", "q", "tl", "w") and "\n\n" in text[start:end]:
                    problems.append(f"{label} {v[1]}: a {kind} span runs across a paragraph break")
            sections.append((v[1], text, marks))
        units.append((label, sections))
    if write(meta, units) != usfm:
        problems.append("does not read back into exactly the same file")
    return problems
