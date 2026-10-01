"""V2: Extract tab sections, strip conditional wrappers, fix boundaries."""
import re
import os

SRC = 'src/app/admin/countries/page.tsx'
OUT = 'src/app/admin/countries/components'

with open(SRC, encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')

# Tab definitions: (name, line_index_0based_start, line_index_0based_end_exclusive)
tabs = [
    ("overview", 1098, 1161),
    ("tax", 1163, 1338),
    ("logistics_model", 1338, 1525),
    ("logistics_providers", 1525, 1653),
    ("payment_gateways", 1653, 1788),
    ("legal_rules", 1788, 1845),
    ("regions", 1845, 1967),
    ("map", 1967, 2012),
    ("kyc", 2012, 2079),
    ("payout_settings", 2079, 2311),
    ("commission_tiers", 2311, 2409),
    ("category_commissions", 2409, 2557),
    ("feature_flags", 2557, 2656),
    ("staff", 2656, 2777),
    ("communications", 2777, 2788),
    ("promotions", 2788, 2941),
    ("analytics", 2941, 3053),
    ("localization", 3053, 3157),
    ("versions", 3157, 3270),
]

def tab_name_to_component(name):
    return "".join(word.capitalize() for word in name.split("_")) + "Tab"

def is_comment_line(line):
    stripped = line.strip()
    return stripped.startswith('/*') or stripped.startswith('//') or stripped.startswith('{/*')

def extract_inner_jsx(raw_lines):
    """Strip the `{activeTab === "xxx" && (` opening and `)}` closing."""
    if not raw_lines:
        return ""
    
    # First line is the conditional opener
    first = raw_lines[0]
    # Find where the JSX starts after `{activeTab === "x" && (`
    idx = first.find('&& (')
    if idx >= 0:
        # Everything after '&& (' is the first line of content
        # But `&& (` might have nothing after it (content on next line)
        rest = first[idx + 4:].strip()
        first_line = rest if rest else ''
    else:
        first_line = first
    
    # Last line is the closing `)}`
    last = raw_lines[-1].rstrip()
    if last == ')}':
        last_line = ''
    elif last.endswith(')}'):
        # e.g. `</section>              )}`
        last_line = last[:-2].rstrip()
    else:
        last_line = last
    
    # Middle lines stay as-is
    middle = raw_lines[1:-1]
    
    result = []
    if first_line:
        result.append(first_line)
    result.extend(middle)
    if last_line:
        result.append(last_line)
    
    # Strip empty lines from start and end
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop(-1)
    
    return result

def extract_additional_imports(tab_name, tab_lines):
    """Check if the tab JSX uses components that need additional imports."""
    combined = '\n'.join(tab_lines)
    needed = []
    
    if 'InternalCommunicationsSystem' in combined:
        needed.append('import InternalCommunicationsSystem from "@/components/country/InternalCommunicationsSystem";')
    if 'CountryMapView' in combined:
        needed.append('import CountryMapView from "@/components/country/CountryMapView";')
    if 'CountryLedgerTable' in combined:
        needed.append('import CountryLedgerTable from "../CountryLedgerTable";')
    if 'PanelTabs' in combined:
        needed.append('import { PanelTabs } from "@/components/PanelPage";')
    if 'PieChartComponent' in combined or 'BarChartComponent' in combined or 'formatNumber' in combined:
        needed.append('import { formatNumber, PieChartComponent, BarChartComponent } from "@/components/ChartComponents";')
    if 'apiFetch' in combined or 'parseJsonResponse' in combined:
        needed.append('import { apiFetch, parseJsonResponse } from "@/lib/api";')
    if 'toErrorMessage' in combined or 'formatIso' in combined or 'toNumberOrNull' in combined:
        needed.append('import { toErrorMessage, toNumberOrNull, formatIso } from "../constants";')
    if 'useToastStore' in combined:
        needed.append('import { useToastStore } from "@/lib/toastStore";')
    
    return needed

os.makedirs(OUT, exist_ok=True)

for name, start, end in tabs:
    component_name = tab_name_to_component(name)
    
    raw_lines = lines[start:end]
    inner_lines = extract_inner_jsx(raw_lines)
    
    # Build the component file
    comp_lines = []
    comp_lines.append('"use client";')
    comp_lines.append('')
    comp_lines.append('import { Fragment } from "react";')
    
    # Add additional imports based on what the tab uses
    extra_imports = extract_additional_imports(name, inner_lines)
    comp_lines.extend(extra_imports)
    
    comp_lines.append('import { Button } from "@/components/ui/Button";')
    comp_lines.append('import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";')
    comp_lines.append('import type { CountriesTabProps } from "./CountriesTabProps";')
    comp_lines.append('')
    comp_lines.append(f'export default function {component_name}({{')
    comp_lines.append('  ...p')
    comp_lines.append(f'}}: CountriesTabProps) {{')
    comp_lines.append('  return (')
    
    # Add the JSX content
    if inner_lines:
        # The indentation in the original file is 14 spaces. Reduce it.
        min_indent = float('inf')
        for line in inner_lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent == float('inf'):
            min_indent = 14
        
        for line in inner_lines:
            if line.strip():
                comp_lines.append('  ' + line[min_indent:] if len(line) > min_indent else '  ' + line.lstrip())
            else:
                comp_lines.append('')
    else:
        comp_lines.append('    <div>Empty tab content</div>')
    
    comp_lines.append('  );')
    comp_lines.append('}')
    comp_lines.append('')
    
    filepath = os.path.join(OUT, f'{component_name}.tsx')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(comp_lines))
    
    print(f'Created {component_name}.tsx ({len(inner_lines)} lines of JSX)')

print(f'\nDone! Created {len(tabs)} component files.')
