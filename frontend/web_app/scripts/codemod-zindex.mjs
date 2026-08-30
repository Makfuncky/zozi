import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
const root = join(process.cwd(), "src");
const map = [
  [/z-\[200\]/g,  "z-modal"],
  [/z-200/g,      "z-toast"],
  [/z-\[999\]/g,  "z-modal"],
  [/z-\[300\]/g,  "z-dropdown"],
];
let count = 0;
function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".tsx") || entry.name.endsWith(".ts")) {
      let src = readFileSync(full, "utf8");
      let changed = false;
      for (const [re, replacement] of map) {
        if (re.test(src)) { src = src.replace(re, replacement); changed = true; }
      }
      if (changed) { writeFileSync(full, src); count++; }
    }
  }
}
walk(root);
console.log(`Z-index codemod complete. Modified ${count} files.`);
