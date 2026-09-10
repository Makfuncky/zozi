import bcrypt

# Current hash in DB
hashed = '$2b$12$gQ0kYWZEx7GU4KH/3C5rd.8e.N54KcWsla3NALnNwoz9GQlXtqOGa'

# Hash from JSON file
json_hash = '$2b$12$LJ3m4ys3Lk0TSwMCkW/YnOYHhMHXLQn2F1qVX7YQvCxhO3eG0Iu1K'

passwords = [
    'logistics123',
    'admin123',
    'password',
    'test123',
    'logistics',
    'T3st_Log!stics_Secure#2024',
]

print('Testing against current DB hash:')
for pw in passwords:
    try:
        result = bcrypt.checkpw(pw.encode(), hashed.encode())
        print(f'  {pw}: {result}')
    except Exception as e:
        print(f'  {pw}: error - {e}')

print('\nTesting against JSON file hash:')
for pw in passwords:
    try:
        result = bcrypt.checkpw(pw.encode(), json_hash.encode())
        print(f'  {pw}: {result}')
    except Exception as e:
        print(f'  {pw}: error - {e}')
