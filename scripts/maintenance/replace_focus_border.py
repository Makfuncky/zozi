from pathlib import Path

root = Path(__file__).resolve().parent.parent / "frontend"
pattern = "focus:border-indigo-500"
replacement = "focus:border-[var(--color-brand)]"

count_files = 0
count_repl = 0
for path in root.rglob('*.tsx'):
    text = path.read_text(encoding='utf-8')
    if pattern in text:
        new = text.replace(pattern, replacement)
        if new != text:
            path.write_text(new, encoding='utf-8')
            count_files += 1
            count_repl += text.count(pattern)

print(f"Updated {count_files} files; {count_repl} replacements")
