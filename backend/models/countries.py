# Re-export shim.
#
# Model definitions for the country/geography domain now live in
# ``models.geography.countries`` (reorg into domain folders). This thin shim
# keeps ``from models.countries import *`` working without re-defining tables
# on the shared ``MetaData`` (which caused "Table already defined" on import).
from models.geography.countries import *  # noqa: F401,F403
from models.geography.countries import __all__  # noqa: F401
