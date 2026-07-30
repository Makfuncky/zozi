
lines = [
    'print(1)',
    'print(2)',
]
with open('out.txt', 'w') as f:
    f.write(chr(10).join(lines))


