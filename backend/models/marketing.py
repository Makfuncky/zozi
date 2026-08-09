# Re-export shim.
#
# Marketing-domain model definitions now live in ``models.comms.marketing`` (reorg
# into domain folders). This thin shim keeps ``from models.marketing import *`` working
# without re-defining tables on the shared ``MetaData``.
from models.comms.marketing import *  # noqa: F401,F403
from models.comms.marketing import __all__  # noqa: F401
