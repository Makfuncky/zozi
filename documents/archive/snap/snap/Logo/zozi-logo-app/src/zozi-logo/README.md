# zozi-logo

Self-contained animated Zozi logo component. Drop this folder into any React project and render the logo with **one line of code**.

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

## Step 3 — One line of code

```tsx
import ZoziLogo from "./components/zozi-logo";

// Anywhere in your JSX:
<ZoziLogo />
```

That is it. The logo renders with its full animation.

---

## Theme support (light / dark)

Use the `theme` prop to match your website's colour scheme:

```tsx
{/* White / light background page */}
<ZoziLogo theme="light" />

{/* Black / dark background page */}
<ZoziLogo theme="dark" />
```

---

## All props

| Prop        | Type                  | Default     | Description                                       |
|-------------|-----------------------|-------------|---------------------------------------------------|
| `theme`     | `"light"` \| `"dark"` | `"light"`   | Adapts colours for light or dark backgrounds.     |
| `size`      | `number`              | `190`       | Logo width in px. Height scales automatically.    |
| `animated`  | `boolean`             | `true`       | Pass `false` for a static, no-animation version. |
| `className` | `string`              | —           | Optional CSS class on the wrapper `<div>`.        |

---

## Notes

- No Tailwind required — works in any React project.
- Safe to use multiple times on the same page (SVG ids are unique per instance).
- Requires React 18+ and the `motion` package.
