const fs = require('fs');
const path = require('path');
function walk(d) {
  let r = [];
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      if (f === '.next' || f === 'node_modules') continue;
      r = r.concat(walk(p));
    } else if (/\.(ts|tsx)$/.test(f)) {
      r.push(p);
    }
  }
  return r;
}
const set = new Set();
const re = /import\s+(?:type\s+)?\{([^}]+)\}\s*from\s*["']lucide-react["']/g;
for (const f of walk('src')) {
  const c = fs.readFileSync(f, 'utf8');
  let m;
  while ((m = re.exec(c))) {
    m[1].split(',').forEach((x) => {
      const n = x.replace(/as\s+\w+/, '').trim();
      if (n && n !== '*' && n !== 'LucideIcon' && !/^(export|type)$/.test(n)) set.add(n);
    });
  }
}
const names = [...set].sort();
const lines = names.map((n) => `  export const ${n}: LucideIcon;`).join('\n');
const decl = `// Ambient module declaration for \`lucide-react\`.
//
// The pinned dependency (lucide-react@1.25.0 per package-lock.json) no longer
// ships its TypeScript declarations in the published tarball, so TypeScript
// (strict mode, noImplicitAny) reports TS7016 for the module and TS2693
// ("Cannot use namespace 'LucideIcon' as a type") for the \`LucideIcon\` type
// that \`src/lib/icons.ts\` re-exports. At runtime the package resolves to its
// CJS/ESM build normally (Next.js compiles via SWC, which does not require
// these .d.ts files). This declaration restores type-checking / next-build
// without changing runtime behavior. The named exports below are every icon
// the app imports (directly or via \`src/lib/icons.ts\`).
declare module "lucide-react" {
  import type { ComponentType, SVGProps } from "react";

  export type LucideIcon = ComponentType<SVGProps<SVGSVGElement>>;
${lines}

  // Icon is imported as a type alias in some components; expose it as the same component type.
  export type Icon = LucideIcon;

  const _default: Record<string, LucideIcon>;
  export default _default;
}
`;
fs.writeFileSync('types/lucide-react.d.ts', decl);
console.log('Wrote', names.length, 'icon declarations');
