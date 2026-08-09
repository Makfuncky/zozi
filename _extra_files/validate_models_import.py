import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import models
print("models import OK; tables:", len(models.Base.metadata.tables))
import data.models
print("data.models import OK")
