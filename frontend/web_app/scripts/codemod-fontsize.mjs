import { readdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
const root = join(process.cwd(), "src");
const map = [
  [/text-\[10px\]/g, "text-xs"],
  [/text-\[9px\]/g,  "text-3xs"],
  [/text-\[8px\]/g,  "text-4xs"],
  [/text-\[7px\]/g,  "text-5xs"],
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
console.log(`Font-size codemod complete. Modified ${count} files.`);
