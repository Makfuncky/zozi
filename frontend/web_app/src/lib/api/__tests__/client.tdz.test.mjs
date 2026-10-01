/**
 * Compile-time + smoke regression test for the apiFetch TDZ bug.
 *
 * Phase 5G regression surfaced:
 *     ReferenceError: Cannot access 'method' before initialization
 *     in apiFetch (frontend/web_app/src/lib/api/client.ts)
 *
 * The root cause was: line 109 logged `method` before line 112 declared it.
 *
 * This test pins the contract by parsing the source file with Node and
 * confirming that the `const method` declaration appears textually before
 * any other reference to `method`.  It is intentionally a source-level
 * assertion so that it fails the moment someone re-introduces the TDZ
 * pattern, even before runtime tests are wired up.
 *
 * Run with: `node frontend/web_app/src/lib/api/__tests__/client.tdz.test.mjs`
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { strict as assert } from "node:assert";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const clientPath = path.resolve(__dirname, "..", "client.ts");

const source = fs.readFileSync(clientPath, "utf8");

// Locate the `apiFetch` function definition.  We find the start via a
// simple regex, then walk braces to find the matching close — the body
// has nested functions so a non-greedy regex is unreliable.  The brace
// walker has to skip past the function-signature braces (e.g. `RequestInit
// & { ... } = {}`) because those are inside the parameter list, before
// the function body actually begins.
const startMatch = source.match(/export async function apiFetch\s*\(/);
assert.ok(startMatch, "Could not find `export async function apiFetch(` in client.ts");

// Find the opening brace of the function body.  Walk forward past the
// parameter list and the return-type annotation, looking for the next `{`
// after the closing `)` of the parameter list.
let parenDepth = 0;
let bodyOpenIdx = -1;
for (let i = startMatch.index; i < source.length; i++) {
    const ch = source[i];
    if (ch === "(") parenDepth++;
    else if (ch === ")") {
        parenDepth--;
        if (parenDepth === 0) {
            // The first `{` after this `)` (allowing only whitespace
            // between) is the function body.
            for (let j = i + 1; j < source.length; j++) {
                const cj = source[j];
                if (cj === "{") {
                    bodyOpenIdx = j;
                    break;
                }
                if (cj !== " " && cj !== "\n" && cj !== "\t" && cj !== "\r") {
                    // Saw non-whitespace before `{` — could be a return
                    // type annotation like `): Promise<Response> {`.
                    // Continue scanning: the body brace must still come.
                }
            }
            break;
        }
    }
}
assert.ok(bodyOpenIdx >= 0, "Could not locate apiFetch function body open brace");

let depth = 0;
let bodyEnd = -1;
for (let i = bodyOpenIdx; i < source.length; i++) {
    const ch = source[i];
    if (ch === "{") depth++;
    else if (ch === "}") {
        depth--;
        if (depth === 0) {
            bodyEnd = i + 1;
            break;
        }
    }
}
assert.ok(bodyEnd > bodyOpenIdx, "Could not brace-match apiFetch body");

const fnBody = source.slice(startMatch.index, bodyEnd);

// Find the declaration of `const method = ...` inside apiFetch.
const declarationIdx = fnBody.search(/const\s+method\s*=/);
assert.ok(
    declarationIdx >= 0,
    "apiFetch must declare `const method = ...` somewhere in its body",
);

// Find every standalone identifier reference to `method` (i.e. not as a
// property like `fetchOptions.method`).  We use a manual word boundary
// instead of `\b` because Node-on-Windows has flaky regex word-boundary
// handling in some contexts.
const refs = [];
const idRe = /(^|[^A-Za-z0-9_$.])method(?![A-Za-z0-9_$])/g;
let m;
while ((m = idRe.exec(fnBody))) {
    refs.push(m.index + m[0].length - "method".length);
}
assert.ok(
    refs.length >= 1,
    "Expected at least one standalone reference to the local `method` inside apiFetch",
);

// No standalone `method` reference may appear BEFORE its declaration —
// that would be a TDZ bug (the exact Phase 5G regression).  Property
// accesses like `fetchOptions.method` are excluded by the regex.
const offending = refs.filter((idx) => idx < declarationIdx);
assert.equal(
    offending.length,
    0,
    `TDZ bug: standalone \`method\` referenced before its declaration. ` +
    `declaration at ${declarationIdx}, offending refs at ${JSON.stringify(offending)}`,
);

console.log(
    `[ok] apiFetch declares \`const method\` at body index ${declarationIdx} ` +
    `before any standalone reference (${refs.length} references, 0 before declaration)`,
);
