# Re-export shim.
#
# Supplier-domain model definitions now live in ``models.comms.suppliers`` (reorg into
# domain folders). This thin shim keeps ``from models.suppliers import *`` working without
# re-defining tables on the shared ``MetaData``.
from domains.comms.models.suppliers import *
from domains.comms.models.suppliers import __all__
