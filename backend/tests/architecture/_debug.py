src = open('tests/architecture/test_law8_through_law18.py').read()
count = src.count('"""')
print(f'Triple quote count: {count}')
pos = 0
positions = []
while True:
    pos = src.find('"""', pos)
    if pos == -1:
        break
    positions.append(pos)
    pos += 3
print(f'Positions: {positions}')
for p in positions:
    line = src[:p].count('\n') + 1
    context = src[max(0,p-30):p+3]
    print(f'  pos {p} (line {line}): ...{repr(context)}...')
