import fs from "fs";
import path from "path";

/**
 * Design-system token regression (DS12 — token source).
 * Guards the contract that the orphaned token system in `styles/tokens.css`
 * is wired into the app (globals.css + layout.tsx) and that tailwind maps
 * utility classes onto the CSS variables it defines.
 */
const STYLES = path.join(__dirname, "..", "styles");
const globals = fs.readFileSync(path.join(STYLES, "globals.css"), "utf8");
const tokens = fs.readFileSync(path.join(STYLES, "tokens.css"), "utf8");
const layout = fs.readFileSync(path.join(__dirname, "..", "app", "layout.tsx"), "utf8");
const tailwind = fs.readFileSync(path.join(__dirname, "..", "..", "tailwind.config.js"), "utf8");

describe("design-system token source (DS12)", () => {
  it("wires tokens.css into globals.css", () => {
    expect(globals).toMatch(/@import\s+["']\.\/tokens\.css["']/);
  });

  it("imports tokens.css from the root layout", () => {
    expect(layout).toMatch(/@\/styles\/tokens\.css/);
  });

  it("defines the radius scale (DS09)", () => {
    for (const r of ["sm", "md", "lg", "xl", "2xl", "pill"]) {
      expect(tokens).toMatch(new RegExp(`--zozi-radius-${r}:`));
    }
  });

  it("defines the elevation scale (DS11)", () => {
    for (const e of ["sm", "md", "lg", "xl"]) {
      expect(tokens).toMatch(new RegExp(`--zozi-elevation-${e}:`));
    }
    expect(tokens).toMatch(/--zozi-ring:/);
  });

  it("defines the motion duration scale (DS16)", () => {
    for (const d of ["fast", "base", "normal", "slow", "slower", "slowest"]) {
      expect(tokens).toMatch(new RegExp(`--zozi-duration-${d}:`));
    }
  });

  it("defines the spacing scale (DS08)", () => {
    for (const s of ["1", "2", "4", "6", "8", "12", "16"]) {
      expect(tokens).toMatch(new RegExp(`--zozi-space-${s}:`));
    }
  });

  it("defines overlay RGB layers used to remove hardcoded colors (DS03/DS04)", () => {
    expect(tokens).toMatch(/--zozi-ov-white-rgb:/);
    expect(tokens).toMatch(/--zozi-ov-ink900-rgb:/);
  });

  it("tailwind maps radius utilities onto the token variables", () => {
    for (const r of ["sm", "md", "lg", "xl", "2xl"]) {
      expect(tailwind).toMatch(new RegExp(`var\\(--zozi-radius-${r}\\)`));
    }
  });

  it("tailwind maps motion durations onto the token variables (DS16)", () => {
    for (const d of ["fast", "base", "normal", "slow", "slower", "slowest"]) {
      expect(tailwind).toMatch(new RegExp(`var\\(--zozi-duration-${d}\\)`));
    }
  });
});
