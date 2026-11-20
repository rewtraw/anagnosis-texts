"""The profile's invariants on every file in texts/ (PROFILE.md): each names its source and rights, each printed
reference is unique within its unit, and each reads back into sections that write out as exactly the same file.

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
    for problem in usfm_profile.check(Path(f).read_text(encoding="utf-8")):
        bad += 1
        print(f"{Path(f).relative_to(root)}: {problem}")
print(f"{len(files)} files, {bad} problems")
sys.exit(1 if bad or not files else 0)
