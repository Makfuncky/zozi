import os
cand = os.path.join("scripts","system_trackers","database_audit.py")
print("exists:", os.path.exists(cand), "abs:", os.path.abspath(cand))
# also locate via walk
for dp,_,fns in os.walk("scripts"):
    if "database_audit.py" in fns:
        print("found:", os.path.abspath(os.path.join(dp,"database_audit.py")))
