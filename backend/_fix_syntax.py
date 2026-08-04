from pathlib import Path

path = r'backend\services\supplier\supplier_countries_service.py'
p = Path(path)
content = p.read_text(errors='replace')
lines = content.split('\n')

# Fix line 473 (0-indexed: 472) - remove dangling minus
lines[472] = '        country.consumer_protection_days = int(payload["consumer_protection_days"])'

result = '\n'.join(lines)
p.write_text(result, encoding='utf-8')
print('Fixed line 473:', lines[472])
