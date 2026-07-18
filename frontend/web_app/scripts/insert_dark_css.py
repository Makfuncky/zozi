from pathlib import Path
p = Path('src/styles/globals.css')
text = p.read_text(encoding='utf-8')
needle = "    radial-gradient(circle at 50% 100%, rgba(30, 58, 138, 0.12), transparent 55%);\n}\n\n\n\nhtml {"
if needle not in text:
    print('needle not found; no update')
    raise SystemExit(1)
replacement = "    radial-gradient(circle at 50% 100%, rgba(30, 58, 138, 0.12), transparent 55%);\n}\n\n.dark {\n  --color-surface-0: #000000;\n  --color-surface-1: #111111;\n  --color-surface-2: #1A1A1A;\n  --color-surface-3: #2A2A2A;\n\n  --color-border: #333333;\n  --color-border-light: #4A4A4A;\n\n  --color-text: #FFFFFF;\n  --color-text-muted: #D1D5DB;\n  --color-text-faint: #9CA3AF;\n\n  --color-glass-base: rgba(0, 0, 0, 0.40);\n  --color-glass-mid: rgba(0, 0, 0, 0.46);\n  --color-glass-hi: rgba(0, 0, 0, 0.52);\n  --color-glass-solid: rgba(0, 0, 0, 0.65);\n  --color-glass-panel: rgba(0, 0, 0, 0.40);\n  --color-glass-faint: rgba(255, 255, 255, 0.08);\n  --color-glass-border: rgba(255, 255, 255, 0.15);\n  --color-glass-border-mid: rgba(255, 255, 255, 0.12);\n  --color-glass-border-soft: rgba(255, 255, 255, 0.08);\n}\n\nhtml {"
text2 = text.replace(needle, replacement)
p.write_text(text2, encoding='utf-8')
print('inserted .dark block')
