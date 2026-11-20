// Every file parsed by an independent USFM parser (usfm-grammar) and converted to USJ, the JSON form of USFM.
//   npm ci && node tools/validate.mjs [--usj out/] [file.usfm or folder …]   (default: every texts/<edition>/)
import pkg from "usfm-grammar";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
const { USFMParser } = pkg;
const root = join(dirname(new URL(import.meta.url).pathname), "..");
const args = process.argv.slice(2);
const out = args.includes("--usj") ? args[args.indexOf("--usj") + 1] : null;
const named = args.filter((a, i) => a !== "--usj" && args[i - 1] !== "--usj");
// A file's edition: its folder, or for corpora/<edition>/usfm/<file>, the folder above.
const edition = (path) => basename(dirname(path)) === "usfm" ? basename(dirname(dirname(path))) : basename(dirname(path));
const files = (named.length ? named : readdirSync(join(root, "texts")).map((d) => join(root, "texts", d)))
  .flatMap((p) => p.endsWith(".usfm") ? [p] : readdirSync(p).filter((f) => f.endsWith(".usfm")).map((f) => join(p, f)));
let bad = 0;
for (const path of files) {
  const dir = edition(path), file = basename(path);
  const parser = new USFMParser(readFileSync(path, "utf8"));
  try {
    const usj = parser.toUSJ();
    if (parser.errors?.length) throw new Error(JSON.stringify(parser.errors.slice(0, 3)));
    if (out) { mkdirSync(join(out, dir), { recursive: true }); writeFileSync(join(out, dir, basename(file, ".usfm") + ".json"), JSON.stringify(usj)); }
  } catch (e) {
    bad++;
    console.log(`${dir}/${file}: ${String(e.message ?? e).slice(0, 400)}`);
  }
}
console.log(`${files.length} files parsed by usfm-grammar, ${bad} with errors`);
process.exit(bad || !files.length ? 1 : 0);
