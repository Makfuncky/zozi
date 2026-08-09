src = open('scripts/system_trackers/system_architecture_audit.py', encoding='utf-8', errors='replace').read()
for kw in ['"red"', '"yellow"', '"advisory"', 'SEVERITY', 'severity_of', 'self.sev', 'def sev']:
    print('==', kw, src.count(kw))
i = src.find('class Finding')
print('---Finding class---')
print(src[i:i+700])
# how is sev set from code?
j = src.find('.sev =')
print('--- sample .sev assignment ---')
print(src[j-120:j+120])
