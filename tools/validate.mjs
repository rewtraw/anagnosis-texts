// Every file parsed by an independent USFM parser (usfm-grammar) and converted to USJ, the JSON form of USFM.
//   npm ci && node tools/validate.mjs [--usj out/]
import pkg from "usfm-grammar";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
const { USFMParser } = pkg;
const root = join(dirname(new URL(import.meta.url).pathname), "..");
const out = process.argv.includes("--usj") ? process.argv[process.argv.indexOf("--usj") + 1] : null;
let bad = 0, n = 0;
for (const dir of readdirSync(join(root, "texts"))) {
  for (const file of readdirSync(join(root, "texts", dir)).filter((f) => f.endsWith(".usfm"))) {
    n++;
    const parser = new USFMParser(readFileSync(join(root, "texts", dir, file), "utf8"));
    try {
      const usj = parser.toUSJ();
      if (parser.errors?.length) throw new Error(JSON.stringify(parser.errors.slice(0, 3)));
      if (out) { mkdirSync(join(out, dir), { recursive: true }); writeFileSync(join(out, dir, basename(file, ".usfm") + ".json"), JSON.stringify(usj)); }
    } catch (e) {
      bad++;
      console.log(`${dir}/${file}: ${String(e.message ?? e).slice(0, 400)}`);
    }
  }
}
console.log(`${n} files parsed by usfm-grammar, ${bad} with errors`);
process.exit(bad || !n ? 1 : 0);
