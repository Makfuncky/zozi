const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const TARGET_DIRS = ['frontend/mobile_app', 'frontend/shared'];
const exts = ['.ts', '.tsx', '.js', '.jsx'];

// token value -> token path
const spacingMap = {4:'xs',8:'sm',16:'md',24:'lg',32:'xl',48:'2xl',64:'3xl'};
const radiusMap = {4:'sm',8:'md',12:'lg',16:'xl',24:'2xl',9999:'full'};
const fontMap = {11:'xs',13:'sm',15:'base',17:'md',20:'lg',24:'xl',30:'2xl',36:'3xl'};

function walk(dir, cb) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, cb);
    else cb(p);
  }
}

let changedFiles = [];

for (const d of TARGET_DIRS) {
  const full = path.join(ROOT, d);
  if (!fs.existsSync(full)) continue;
  walk(full, (file) => {
    if (!exts.includes(path.extname(file))) return;
    let src = fs.readFileSync(file, 'utf8');
    // only touch files that reference theme (safe guard)
    if (!/useThemeStore|const\s*\{\s*theme\s*\}|makeStyles\(/.test(src)) return;

    let out = src;

    // helper to replace a property:value number when the number maps
    function replaceMap(propList, map, template) {
      for (const [num, token] of Object.entries(map)) {
        const props = propList.join('|');
        // patterns like fontSize: 16, or fontSize:16,
        const re = new RegExp(`(\\b(?:${props})\\s*:\\s*)${num}(\\s*)([,}])`, 'g');
        out = out.replace(re, (m, p1, p2, p3) => {
          // leave if already contains theme
          if (p1.includes('theme') || p1.includes('s.')) return m;
          return `${p1}${template.replace('{token}', token)}${p2}${p3}`;
        });
      }
    }

    replaceMap(['padding','paddingVertical','paddingHorizontal','paddingLeft','paddingRight','paddingTop','paddingBottom','margin','marginVertical','marginHorizontal','marginLeft','marginRight','marginTop','marginBottom','gap','paddingHorizontal'], spacingMap, 'theme.spacing.{token}');
    replaceMap(['borderRadius','borderTopLeftRadius','borderTopRightRadius','borderBottomLeftRadius','borderBottomRightRadius'], radiusMap, 'theme.radius.{token}');
    replaceMap(['fontSize','fontSizeRem','fontSizeSp'], fontMap, 'theme.fontSize.{token}');
    // width/height/minWidth/minHeight when matching spacing
    replaceMap(['width','height','minWidth','minHeight','maxWidth','maxHeight'], spacingMap, 'theme.spacing.{token}');

    if (out !== src) {
      fs.writeFileSync(file, out, 'utf8');
      changedFiles.push(file);
    }
  });
}

console.log('Updated files:', changedFiles.length);
for (const f of changedFiles) console.log(' -', path.relative(ROOT, f));

if (changedFiles.length === 0) process.exit(0);
else process.exit(0);