# Re-export shim.
#
# Model definitions for the country-enhancements domain now live in
# ``models.geography.country_enhancements`` (reorg into domain folders). This
# thin shim keeps ``from models.country_enhancements import *`` working
# without re-defining tables on the shared ``MetaData`` (which caused "Table
# already defined" on import).
from _legacy.models.geography.country_enhancements import *  # noqa: F401,F403
from _legacy.models.geography.country_enhancements import __all__  # noqa: F401
