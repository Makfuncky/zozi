import os
os.environ['FIELD_ENCRYPTION_SALT'] = 'abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789'
from backend.main import app
print(len(app.routes))
