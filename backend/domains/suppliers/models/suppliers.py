# Re-export shim.
#
# Supplier-domain model definitions now live in ``models.comms.suppliers`` (reorg into
# domain folders). This thin shim keeps ``from models.suppliers import *`` working without
# re-defining tables on the shared ``MetaData``.
from models.comms.suppliers import *  # noqa: F401,F403
from models.comms.suppliers import __all__  # noqa: F401
