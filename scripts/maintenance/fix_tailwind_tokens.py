#!/usr/bin/env python3
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "frontend"
patterns = [
    (re.compile(r"\btext-\(\-\-color-([^)]+)\)"), r"text-[var(--color-\1)]"),
    (re.compile(r"\bbg-\(\-\-color-([^)]+)\)"), r"bg-[var(--color-\1)]"),
    (re.compile(r"\bborder-\(\-\-color-([^)]+)\)"), r"border-[var(--color-\1)]"),
    (re.compile(r"\bplaceholder:text-\(\-\-color-([^)]+)\)"), r"placeholder:text-[var(--color-\1)]"),
    (re.compile(r"\bhover:text-\(\-\-color-([^)]+)\)"), r"hover:text-[var(--color-\1)]"),
    (re.compile(r"\bhover:bg-\(\-\-color-([^)]+)\)"), r"hover:bg-[var(--color-\1)]"),
    (re.compile(r"\bring-\(\-\-color-([^)]+)\)"), r"ring-[var(--color-\1)]"),
]

count_files = 0
count_replacements = 0
for path in root.rglob('*'):
    if path.is_file() and path.suffix in {'.tsx', '.ts', '.jsx', '.js', '.css'}:
        text = path.read_text(encoding='utf-8')
        new_text = text
        for pat, rep in patterns:
            new_text, n = pat.subn(rep, new_text)
            count_replacements += n
        if new_text != text:
            path.write_text(new_text, encoding='utf-8')
            count_files += 1

print(f"Updated {count_files} files with {count_replacements} replacements")
