import bcrypt

# The current hash in the database
hashed = '$2b$10$El6l73Ftq1prQ.oCuq71QODX9x4YXHHKLK7xN0OF8tX0c2PpEKzcG'

# Try many possible passwords
passwords = [
    'logistics123',
    'T3st_Log!stics_Secure#2024',
    'admin123',
    'password',
    'logistics',
    'Password1',
    'password123',
    'admin',
    'test123',
    'test',
    '123456',
    'logistics2024',
    'Logistics123',
    'LOGISTICS123',
    'admin@zozi.com',
    'logistics@zozi.com',
    'secret',
    'pass123',
    'logistics!',
    'P@ssw0rd',
    'logistics1',
    'logistics01',
]

for pw in passwords:
    try:
        if bcrypt.checkpw(pw.encode(), hashed.encode()):
            print(f'MATCH: {pw}')
            break
    except:
        pass
else:
    print('No match found')
