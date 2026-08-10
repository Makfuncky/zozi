#!/usr/bin/env python3
"""DBA04 fix: unify country_code width to String(3).

The FK target country_configs.code is String(3); the many String(10)
country_code columns that reference it are a latent Postgres FK type
mismatch (VARCHAR(10) cannot reference VARCHAR(3)). Standardize on
String(3) (ISO 3166 alpha-3) everywhere.
Scope: only lines assigning a country_code/origin/destination country
column, so other String(10) columns are untouched.
"""
import glob
import re

PAT = re.compile(r"((?:origin_|destination_)?country_code = Column\(String\()\d+")


def main():
    files = sorted(set(glob.glob("backend/models/**/*.py", recursive=True) +
                       glob.glob("backend/models/*.py")))
    changed = 0
    for f in files:
        if f.endswith("__init__.py"):
            continue
        with open(f, encoding="utf-8") as fh:
            lines = fh.readlines()
        new = []
        file_changed = False
        for ln in lines:
            if PAT.search(ln):
                ln = PAT.sub(r"\g<1>3", ln)
                file_changed = True
            new.append(ln)
        if file_changed:
            with open(f, "w", encoding="utf-8") as fh:
                fh.writelines(new)
            changed += 1
            print("OK  ", f)
    print(f"\nTOTAL changed files: {changed}")


if __name__ == "__main__":
    main()
