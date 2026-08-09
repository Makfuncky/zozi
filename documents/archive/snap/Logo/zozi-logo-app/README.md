# Zozi Logo Package

The animated Zozi brand components are in the `zozi-logo` folder.

Copy the entire `zozi-logo` folder into your React website and follow the instructions in `zozi-logo/README.md`.

## Quick start

1. Copy `zozi-logo/` to your project (e.g., `src/components/zozi-logo/`).
2. `npm install motion`
3. `<ZoziLogo />` in your JSX.
4. Or use `<ZoziWordmark />` for the pin-free “Zozi” version.

## Recording the animation

From the project root, run:

```bash
npm install --save-dev playwright
npm run record-wordmark
```

If port `5173` is already in use, run with an alternate port:

```powershell
$env:PORT='5180'; npm run record-wordmark
```

The captured `webm` file will be written to the `recordings/` folder.
