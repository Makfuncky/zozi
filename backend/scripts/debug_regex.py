import re
text = '''class SystemAlert(Base):
    __tablename__ = "system_alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False)
'''
m = re.search(r'class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', text)
print('match:', repr(m.group(0)))
print('end:', m.end())
print('remaining start:', repr(text[m.end():]))
