import re, glob

pat = re.compile(r'__table_args__\s*=.*\{[^{}]*["\']schema["\'][^{}]*\}')
for f in sorted(glob.glob('models/**/*.py', recursive=True)):
    lines = open(f, encoding='utf-8').read().splitlines()
    for i, line in enumerate(lines, 1):
        if '__table_args__' in line and 'schema' in line:
            m = pat.search(line)
            if not m:
                continue
            # get the dict substring
            dictstr = m.group(0)[m.group(0).index('{'):]
            # find the position of the dict end '}' within the full line
            dict_end = line.index(dictstr) + len(dictstr) - 1  # index of closing }
            rest = line[dict_end+1:].strip()
            # if after the dict there is more (a '+' or ',' or ')(' ) then dict is not last
            if rest.startswith('+') or rest.startswith(',') or rest.startswith(')'):
                print(f"{f}:{i}: {line.strip()[:170]}")
