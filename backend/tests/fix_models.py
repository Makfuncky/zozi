import re

# Fix countries.py relationships
fpath = r'D:\Projects/10- E-COMMERCE WEBSITE/zozi/backend/models/countries.py'.replace('/', '\\')
with open(fpath, 'r') as f:
    content = f.read()

old = '    basics = relationship("CountryBasics", back_populates="country")\n\n\n    economics = relationship("CountryEconomics", back_populates="country")\n\n\n    tax = relationship("CountryTax", back_populates="country")\n\n\n    legal = relationship("CountryLegal", back_populates="country")'

new = '    basics = relationship("CountryBasics", back_populates="country", foreign_keys=[basics_id])\n\n    economics = relationship("CountryEconomics", back_populates="country", foreign_keys=[economics_id])\n\n    tax = relationship("CountryTax", back_populates="country", foreign_keys=[tax_id])\n\n    legal = relationship("CountryLegal", back_populates="country", foreign_keys=[legal_id])'

if old in content:
    content = content.replace(old, new)
    with open(fpath, 'w') as f:
        f.write(content)
    print("countries.py: FIXED")
else:
    print("countries.py: pattern not found, checking with regex...")
    # Try to find with flexible whitespace
    pattern = r'basics = relationship\("CountryBasics", back_populates="country"\)'
    matches = re.findall(pattern, content)
    print(f"  Found {len(matches)} matches for basics relationship")
    if matches:
        print(f"  Match: {repr(matches[0])}")
