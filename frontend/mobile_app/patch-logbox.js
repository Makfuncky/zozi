#!/usr/bin/env node
/**
 * Patch @expo/log-box to be compatible with React 18.
 *
 * @expo/log-box@55 is built against React 19 and uses two React 19-only
 * patterns that crash the dev error overlay on React 18:
 *
 *   1. Rendering a Context object directly: <LogContext value={...} />
 *      (React 18 only supports <LogContext.Provider>).
 *   2. Reading context via React.use(Context) (React.use is React 19 only).
 *
 * This script rewrites those usages in the package source so the Expo web
 * dev error overlay works under React 18.2.
 *
 * Re-run after `pnpm install` (it is wired as a postinstall hook).
 */

const fs = require('fs');
const path = require('path');

function hasLogBoxSource(dir) {
  return fs.existsSync(path.join(dir, 'src', 'logbox-dom-polyfill.tsx'));
}

function findLogBoxPackageDirs() {
  const dirs = new Set();

  // 1. Resolve through normal node module resolution (hoisted copy).
  try {
    const pkg = require.resolve('@expo/log-box/package.json', { paths: [__dirname] });
    const resolved = fs.realpathSync(path.dirname(pkg));
    if (hasLogBoxSource(resolved)) dirs.add(resolved);
  } catch (_) {
    /* not resolvable directly */
  }

  // 2. Top-level node_modules/@expo/log-box (pnpm hoist / legacy layout).
  const topLevel = path.join(__dirname, 'node_modules', '@expo', 'log-box');
  if (hasLogBoxSource(topLevel)) dirs.add(fs.realpathSync(topLevel));

  // 3. Every copy in the pnpm virtual store.
  const pnpmRoot = path.join(__dirname, 'node_modules', '.pnpm');
  if (fs.existsSync(pnpmRoot)) {
    for (const entry of fs.readdirSync(pnpmRoot)) {
      if (!entry.startsWith('@expo+log-box@')) continue;
      const candidate = path.join(pnpmRoot, entry, 'node_modules', '@expo', 'log-box');
      if (hasLogBoxSource(candidate)) dirs.add(fs.realpathSync(candidate));
    }
  }

  return Array.from(dirs);
}

function patchFile(file, edits) {
  if (!fs.existsSync(file)) {
    console.log('  skip (missing):', file);
    return false;
  }
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;
  for (const [from, to] of edits) {
    if (content.includes(from)) {
      content = content.split(from).join(to);
      changed = true;
    }
  }
  if (changed) {
    fs.writeFileSync(file, content);
    console.log('  patched:', file);
  } else {
    console.log('  already patched:', file);
  }
  return changed;
}

const dirs = findLogBoxPackageDirs();
if (dirs.length === 0) {
  console.log('@expo/log-box not found; skipping patch.');
  process.exit(0);
}

for (const dir of dirs) {
  console.log('Patching @expo/log-box at:', dir);

  const src = path.join(dir, 'src');

// 1. Direct <LogContext> render -> <LogContext.Provider> in the web polyfill.
patchFile(path.join(src, 'logbox-dom-polyfill.tsx'), [
  ['    <LogContext\n', '    <LogContext.Provider\n'],
  ['    </LogContext>', '    </LogContext.Provider>'],
]);

// 2. React.use(Context) -> React.useContext(Context) in LogBoxLog.
patchFile(path.join(src, 'Data', 'LogBoxLog.ts'), [
  ['React.use(LogContext)', 'React.useContext(LogContext)'],
]);

// 3. use(Context) -> useContext(Context) in context helpers (React.use -> useContext).
patchFile(path.join(src, 'ContextActions.tsx'), [
  ['{ createContext, ReactNode, use }', '{ createContext, ReactNode, useContext }'],
  ['use(ActionsContextProvider)', 'useContext(ActionsContextProvider)'],
]);

  patchFile(path.join(src, 'ContextDevServer.tsx'), [
    ['{ useEffect, useState, createContext, use, ReactNode }',
     '{ useEffect, useState, createContext, useContext, ReactNode }'],
    ['use(DevServerContextProvider)', 'useContext(DevServerContextProvider)'],
  ]);
}

console.log('Done.');
