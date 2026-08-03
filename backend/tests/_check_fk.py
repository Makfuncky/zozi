import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only'

from data.base import Base
import data.models
from data.models import User

for col in User.__table__.columns:
    for fk in col.foreign_keys:
        print('FK:', repr(fk.target_fullname))
        print('  _colspec:', repr(fk._colspec))
        print('  _column_tokens:', repr(fk._column_tokens))
