"""Extract 19 tab sections from countries/page.tsx into separate component files."""
import re
import os

SRC = 'src/app/admin/countries/page.tsx'
OUT = 'src/app/admin/countries/components'

with open(SRC, encoding='utf-8') as f:
    lines = f.readlines()

# Tab definitions: (name, start_line, end_line_exclusive)
# Lines are 1-indexed in the source
tabs = [
    ("overview", 1099, 1162),
    ("tax", 1164, 1339),
    ("logistics_model", 1339, 1526),
    ("logistics_providers", 1526, 1654),
    ("payment_gateways", 1654, 1789),
    ("legal_rules", 1789, 1846),
    ("regions", 1846, 1968),
    ("map", 1968, 2013),
    ("kyc", 2013, 2080),
    ("payout_settings", 2080, 2312),
    ("commission_tiers", 2312, 2410),
    ("category_commissions", 2410, 2558),
    ("feature_flags", 2558, 2657),
    ("staff", 2657, 2778),
    ("communications", 2778, 2789),
    ("promotions", 2789, 2942),
    ("analytics", 2942, 3054),
    ("localization", 3054, 3158),
    ("versions", 3158, 3271),
]

def tab_name_to_component(name):
    """Convert 'logistics_model' to 'LogisticsModelTab'"""
    return "".join(word.capitalize() for word in name.split("_")) + "Tab"

os.makedirs(OUT, exist_ok=True)

for name, start, end in tabs:
    component_name = tab_name_to_component(name)
    
    # Extract the tab JSX (strip the `{activeTab === "xxx" && (` wrapper)
    raw_lines = lines[start-1:end]  # 0-indexed slices
    raw = "".join(raw_lines)
    
    # Remove the opening wrapper: `{activeTab === "xxx" && (`
    # and the closing: `)}`
    # Find the actual JSX content inside
    inner = re.sub(r'^\{activeTab === "[^"]+" &&\s*\(', '', raw)
    # Remove trailing `)}` or `)}` (the closing of the conditional)
    inner = re.sub(r'\)}$', '', inner.rstrip())
    # Also remove trailing `)}` if it has a newline before
    if inner.rstrip().endswith(')}'):
        inner = inner.rstrip()[:-2].rstrip()
    
    # Also try to strip just the trailing `)` and `}` if the above didn't work
    inner = inner.rstrip()
    if inner.endswith(')}'):
        inner = inner[:-2].rstrip()
    
    # Build the component file
    comp_lines = [
        '"use client";',
        '',
        'import { Fragment, useState, useMemo } from "react";',
        'import { Button } from "@/components/ui/Button";',
        'import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";',
        'import type { CountriesTabProps } from "./CountriesTabProps";',
        '',
        f'export default function {component_name}({{',
        '  ...p',
        f'}}: CountriesTabProps) {{',
        '  return (',
        inner,
        '  );',
        '}',
        '',
    ]
    
    filepath = os.path.join(OUT, f'{component_name}.tsx')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(comp_lines))
    
    print(f'Created {filepath} ({end-start} lines)')

print(f'\nDone! Created {len(tabs)} component files.')
