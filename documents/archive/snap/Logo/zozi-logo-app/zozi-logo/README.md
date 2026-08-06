# zozi-logo

Self-contained animated Zozi brand components. Drop this folder into any React project and render either the original pin logo or the pin-free “Zozi” wordmark.

---

## Step 1 — Copy the folder

Copy the entire `zozi-logo` folder into your website, for example:

```
your-website/
  src/
    components/
      zozi-logo/       ← paste here
        ZoziLogo.tsx
        index.ts
        README.md
```

## Step 2 — Install the one dependency

```bash
npm install motion
```

> If your project already uses `framer-motion` or `motion`, you are done — no extra install needed.

## Step 3 — Use either component

```tsx
import ZoziLogo from "./components/zozi-logo";
import { ZoziWordmark } from "./components/zozi-logo";

// Anywhere in your JSX:
<ZoziLogo />

// Pin-free wordmark version:
<ZoziWordmark />
```

That is it. Both components render with their full animation.

---

## Theme support (light / dark)

Use the `theme` prop to match your website's colour scheme:

```tsx
{/* White / light background page */}
<ZoziLogo theme="light" />
<ZoziWordmark theme="light" />

{/* Black / dark background page */}
<ZoziLogo theme="dark" />
<ZoziWordmark theme="dark" />
```

---

## All props

| Prop        | Type                  | Default     | Description                                       |
|-------------|-----------------------|-------------|---------------------------------------------------|
| `theme`     | `"light"` \| `"dark"` | `"light"`   | Adapts colours for light or dark backgrounds.     |
| `size`      | `number`              | `190` / `320` | Width in px. Height scales automatically.      |
| `animated`  | `boolean`             | `true`      | Pass `false` for a static, no-animation version.  |
| `className` | `string`              | —           | Optional CSS class on the wrapper `<div>`.        |

`ZoziLogo` defaults to `190px` wide. `ZoziWordmark` defaults to `320px` wide.

---

## Notes

- No Tailwind required — works in any React project.
- Safe to use multiple times on the same page (SVG ids are unique per instance).
- Requires React 18+ and the `motion` package.
