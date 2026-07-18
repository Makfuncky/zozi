import sys
sys.path.insert(0, '.')
import os
os.environ['APP_ENV'] = 'test'

from db.database import SessionLocal
from models import Product
import re

db = SessionLocal()
products = db.query(Product.name).filter(Product.is_active == True, Product.is_deleted == False).limit(1000).all()

words = set()
for (name,) in products:
    for w in re.findall(r'\b[a-z]+', name.lower()):
        if w.startswith('iph'):
            print(f'Found: {w} in {name}')
        words.add(w)

print(f'Total unique words: {len(words)}')
print(f'Words starting with "iph": {[w for w in words if w.startswith("iph")]}')
db.close()
