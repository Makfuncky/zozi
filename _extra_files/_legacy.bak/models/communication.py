# Re-export shim.
#
# Model definitions for the communication domain now live in
# ``models.comms.communication`` (reorg into domain folders). This thin shim keeps
# ``from models.communication import *`` working without re-defining tables on the
# shared ``MetaData`` (which caused "Table already defined" on import).
from _legacy.models.comms.communication import *  # noqa: F401,F403
from _legacy.models.comms.communication import __all__  # noqa: F401
