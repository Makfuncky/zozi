import bcrypt

password = b'logistics123'
hashed = '$2b$13$wuJF7ZNAyqC4dkkO1SrSVecZeZKFeWlGfgPjui3hCyhM0n4904o7a'
result = bcrypt.checkpw(password, hashed.encode())
print(f'Password "logistics123" matches: {result}')

# Also test the other password
password2 = b'T3st_Log!stics_Secure#2024'
result2 = bcrypt.checkpw(password2, hashed.encode())
print(f'Password "T3st_Log!stics_Secure#2024" matches: {result2}')
