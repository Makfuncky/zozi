import main
from lifespan import _preload_all_models
_preload_all_models()
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
    print("ALL MAPPERS OK")
except Exception as e:
    print("MAPPER ERROR:")
    print(str(e)[:4000])
