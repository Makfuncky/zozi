import bcrypt

# The actual hash from the database
h = '$2b$12$gQ0kYWZEx7GU4KH/3C5rd.8e.N54KcWsla3NALnNwoz9GQlXtqOGa'
print(f'Hash: {h}')
print(f'Length: {len(h)}')

# Check if valid
try:
    result = bcrypt.checkpw(b'test', h.encode())
    print(f'Test result: {result}')
except ValueError as e:
    print(f'ValueError: {e}')

# Try to hash a password and compare format
test_hash = bcrypt.hashpw(b'test', bcrypt.gensalt(rounds=12)).decode()
print(f'\nTest hash format: {test_hash}')
print(f'Test hash length: {len(test_hash)}')
