"""The profile's invariants on every file in texts/ (PROFILE.md): each names its source and rights, each printed
reference is unique within its unit, each reads back into sections that write out as exactly the same file, no
speaker's label, quotation or word crosses a paragraph, and every row of a words/ sidecar names the word that is
there in the text.

    python3 tools/check.py
"""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import usfm_profile  # noqa: E402

root = Path(__file__).resolve().parents[1]
files = sorted(glob.glob(str(root / "texts/*/*.usfm")))
bad = 0
for f in files:
    usfm = Path(f).read_text(encoding="utf-8")
    for problem in usfm_profile.check(usfm):
        bad += 1
        print(f"{Path(f).relative_to(root)}: {problem}")
    sidecar = Path(f).parent / "words" / (Path(f).stem + ".tsv")
    if sidecar.exists():  # every row's word is the word at that place in the text
        for problem in usfm_profile.check_words(usfm, sidecar.read_text(encoding="utf-8")):
            bad += 1
            print(f"{sidecar.relative_to(root)}: {problem}")
print(f"{len(files)} files, {bad} problems")
sys.exit(1 if bad or not files else 0)
