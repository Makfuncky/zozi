from db.database import SessionLocal
from services.commission_engine import seed_defaults, get_global_config
from models import CommissionCategoryRate, CommissionBadgeTier

db = SessionLocal()
seed_defaults(db)
cfg = get_global_config(db)
print('config default_rate:', cfg.default_rate)
cats = db.query(CommissionCategoryRate).count()
badges = db.query(CommissionBadgeTier).count()
print('category rates:', cats, '  badge tiers:', badges)
db.close()
print('Done')

