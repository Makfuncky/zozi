import re
src = open('scripts/system_trackers/system_architecture_audit.py', encoding='utf-8', errors='replace').read()
sevs = set(re.findall(r'\.sev\s*=\s*["\'](\w+)["\']', src))
print('SEVERITIES:', sorted(sevs))
codes = set(re.findall(r'code\s*=\s*["\'](\w+)["\']', src))
print('CODES:', sorted(codes))
# also look at how findings are categorized (check_ functions)
checks = set(re.findall(r'def (check_\w+)', src))
print('CHECKS:', sorted(checks))
