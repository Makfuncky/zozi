import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
print("models import OK, tables=", len(models.Base.metadata.tables))
