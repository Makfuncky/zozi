import infrastructure.database.base as b1
print("canonical Base id", id(b1.Base))
import domains.accounts.models.user as um
print("user module Base id", id(um.Base))
from domains.accounts.models.user import User
print("User.metadata is canonical?", User.metadata is b1.Base.metadata)
print("User tablename", User.__tablename__)
print("users in canonical metadata:", "users" in b1.Base.metadata.tables)
print("user module Base module", um.Base.__module__)
print("User.metadata tables count", len(User.metadata.tables))
print("has email_verified col:", "email_verified" in [c.name for c in User.__table__.columns])
