#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', 'frontend', 'mobile_app');

function walk(dir) {
  const files = [];
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    if (fs.statSync(p).isDirectory()) {
      files.push(...walk(p));
    } else if (/\.(ts|tsx|js|jsx)$/.test(p)) files.push(p);
  }
  return files;
}

function capitalize(s){ return s.charAt(0).toUpperCase()+s.slice(1); }

const files = walk(root);
let changed = 0;
for (const fp of files) {
  let src = fs.readFileSync(fp, 'utf8');
  // find StyleSheet.create declarations with a const
  const re = /const\s+(\w+)\s*=\s*StyleSheet\.create\s*\(/g;
  let m;
  const matches = [];
  while((m = re.exec(src))){ matches.push({name: m[1], idx: m.index}); }
  if (!matches.length) continue;

  // check if the StyleSheet block contains 'theme.' nearby by searching after idx up to next ');'
  let fileChanged = false;
  for (const mm of matches){
    const start = mm.idx;
    const slice = src.slice(start);
    const endIdx = slice.indexOf(');');
    if (endIdx === -1) continue;
    const block = slice.slice(0, endIdx);
    if (!/theme\./.test(block)) continue;

    // replace const <name> = StyleSheet.create( with const create<Name> = (theme) => StyleSheet.create(
    const createName = 'create' + capitalize(mm.name);
    const varRe = new RegExp('const\\s+'+mm.name+'\\s*=\\s*StyleSheet\\.create\\s*\\(');
    src = src.replace(varRe, `const ${createName} = (theme) => StyleSheet.create(`);

    // insert call after first occurrence of "const { theme } = useThemeStore();"
    const themeUse = /const\s*\{\s*theme\s*\}\s*=\s*useThemeStore\s*\(\s*\)\s*;/;
    const themeMatch = src.match(themeUse);
    if (themeMatch) {
      // insert after the theme line
      src = src.replace(themeUse, (m) => `${m}\n  const ${mm.name} = ${createName}(theme);`);
      fileChanged = true;
    } else {
      // if there's no theme usage, skip and revert replacement
      src = src.replace(`const ${createName} = (theme) => StyleSheet.create(`, `const ${mm.name} = StyleSheet.create(`);
    }
  }

  if (fileChanged) {
    fs.writeFileSync(fp, src, 'utf8');
    changed++;
    console.log('Patched', fp);
  }
}

console.log('Done. Files patched:', changed);
