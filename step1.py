import re
path = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\system_architecture_audit.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

def repl(old, new):
    global text
    if old in text:
        text = text.replace(old, new)
    else:
        print("WARN: " + old[:60])

repl('DEFAULT_MIS_HOUSED_CONTROLLERS = {"audit_controllers", "payments_controller", "cache_utils"}\n', '')
repl('DEFAULT_KNOWN_WRITER_CONTROLLERS = {"audit_controller.py"}\n', '')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("step1 done")
