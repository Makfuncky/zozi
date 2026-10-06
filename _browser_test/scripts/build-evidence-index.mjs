#!/usr/bin/env node
/**
 * build-evidence-index — turn one run's evidence tree into a browsable gallery.
 *
 * Input : evidence/<run-id>/<actor>/<nn>-<step>-{before,after}.png  (+ report.md)
 * Output: evidence/<run-id>/index.html
 *
 * Screenshots are linked relatively, so the folder can be zipped and shared.
 * Run: node scripts/build-evidence-index.mjs [run-id]
 */
import { readdir, readFile, writeFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, basename, relative } from "node:path";

const EVIDENCE_DIR = process.env.EVIDENCE_DIR || join(process.cwd(), "evidence");
const runId = process.argv[2] || process.env.RUN_ID;
const runRoot = runId ? join(EVIDENCE_DIR, runId) : null;

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

async function listRuns() {
  if (!existsSync(EVIDENCE_DIR)) return [];
  const out = [];
  for (const e of await readdir(EVIDENCE_DIR, { withFileTypes: true })) {
    if (!e.isDirectory()) continue;
    if (await stat(join(EVIDENCE_DIR, e.name)).then((s) => s.isDirectory())) out.push(e.name);
  }
  return out.sort().reverse();
}

function renderStepShot(file) {
  const name = basename(file);
  const isAfter = /-after\.png$/.test(name);
  const label = name.replace(/^\d+-/, "").replace(/-(before|after)\.png$/, "");
  const cap = `${label} — ${isAfter ? "after" : "before"}`;
  return `<figure><a href="${esc(file)}" target="_blank"><img loading="lazy" src="${esc(file)}" alt="${esc(cap)}"></a><figcaption>${esc(cap)}</figcaption></figure>`;
}

async function renderActor(actor, dir) {
  const files = (await readdir(dir)).sort();
  const shots = files.filter((f) => f.endsWith(".png"));
  const videos = files.filter((f) => /\.(webm|mp4)$/.test(f));
  const reportFile = files.find((f) => f === "report.md");
  const report = reportFile ? await readFile(join(dir, reportFile), "utf-8") : "";

  // Pair before/after under one step heading.
  const steps = new Map();
  for (const s of shots) {
    const key = s.replace(/-(before|after)\.png$/, "");
    if (!steps.has(key)) steps.set(key, []);
    steps.get(key).push(s);
  }

  const sections = [...steps.entries()]
    .map(([key, pair]) => {
      const title = key.replace(/^\d+-/, "").replace(/-/g, " ");
      const imgs = pair
        .sort((a, b) => (a.includes("-after") ? 1 : 0) - (b.includes("-after") ? 1 : 0))
        .map((f) => renderStepShot(`${actor}/${f}`))
        .join("\n");
      return `<section class="step"><h3>${esc(title)}</h3><div class="shots">${imgs}</div></section>`;
    })
    .join("\n");

  const vids = videos
    .map((v) => `<video controls preload="metadata" src="${esc(actor + "/" + v)}"></video>`)
    .join("\n");

  return `<details class="actor" open>
  <summary><strong>${esc(actor)}</strong> — ${steps.size} steps, ${shots.length} screenshots</summary>
  ${vids ? `<div class="videos">${vids}</div>` : ""}
  ${sections}
  ${report ? `<details class="report"><summary>diagnostics report.md</summary><pre>${esc(report)}</pre></details>` : ""}
</details>`;
}

async function build(target) {
  if (!target || !existsSync(target)) {
    console.error(`evidence run not found: ${target ?? "(none)"}`);
    process.exit(1);
  }
  const actors = (await readdir(target, { withFileTypes: true }))
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();

  const runs = await listRuns();
  const body = actors.length
    ? (await Promise.all(actors.map((a) => renderActor(a, join(target, a))))).join("\n")
    : "<p>No actor folders found.</p>";

  const shotCount = (
    await Promise.all(
      actors.map(async (a) => (await readdir(join(target, a))).filter((f) => f.endsWith(".png")).length),
    )
  ).reduce((a, b) => a + b, 0);

  const nav = runs
    .map((r) => `<a href="../${esc(r)}/index.html"${r === basename(target) ? ' class="current"' : ""}>${esc(r)}</a>`)
    .join(" · ");

  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Evidence — ${esc(basename(target))}</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.5 ui-sans-serif,system-ui,sans-serif; margin: 0; padding: 24px; max-width: 1400px; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .meta { color: #666; margin-bottom: 20px; }
  .runs { margin-bottom: 24px; font-size: 12px; }
  .runs a { margin-right: 8px; }
  .runs .current { font-weight: 700; text-decoration: underline; }
  .actor { border: 1px solid #8884; border-radius: 8px; padding: 12px 16px; margin-bottom: 18px; }
  .actor > summary { cursor: pointer; font-size: 15px; }
  .step { margin: 16px 0 8px; }
  .step h3 { font-size: 13px; margin: 0 0 8px; color: #555; text-transform: capitalize; }
  .shots { display: flex; gap: 12px; flex-wrap: wrap; }
  figure { margin: 0; width: 320px; }
  figure img { width: 100%; border: 1px solid #8884; border-radius: 6px; background: #fff; }
  figcaption { font-size: 11px; color: #666; margin-top: 4px; }
  .videos { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
  video { width: 420px; border: 1px solid #8884; border-radius: 6px; }
  pre { background: #8881; padding: 12px; border-radius: 6px; overflow: auto; font-size: 12px; }
  .report > summary { cursor: pointer; font-size: 13px; margin-top: 12px; }
</style></head>
<body>
  <h1>Evidence gallery</h1>
  <div class="meta">run <code>${esc(basename(target))}</code> — ${actors.length} actor(s), ${shotCount} screenshots</div>
  <div class="runs">runs: ${nav}</div>
  ${body}
</body></html>`;

  const out = join(target, "index.html");
  await writeFile(out, html, "utf-8");
  console.log(`wrote ${relative(process.cwd(), out)} — ${actors.length} actors, ${shotCount} screenshots`);
}

const runs = await listRuns();
const target = runRoot || (runs.length ? join(EVIDENCE_DIR, runs[0]) : null);
if (!target) {
  console.error(`no evidence runs under ${EVIDENCE_DIR}`);
  process.exit(1);
}
await build(target);
if (!runId && runs.length > 1) {
  console.log(`(built most recent of ${runs.length} runs; pass a run id to pick another)`);
}
