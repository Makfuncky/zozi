import bcrypt

hashed = '$2b$10$El6l73Ftq1prQ.oCuq71QODX9x4YXHHKLK7xN0OF8tX0c2PpEKzcG'

passwords = [
    'logistics123',
    'T3st_Log!stics_Secure#2024',
    'admin123',
    'password',
    'logistics',
]

for pw in passwords:
    result = bcrypt.checkpw(pw.encode(), hashed.encode())
    print(f'{pw}: {result}')
