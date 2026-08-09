import os
repo = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
print("backend/.env exists:", os.path.exists(os.path.join(repo, "backend", ".env")))
print("backend/.env.local exists:", os.path.exists(os.path.join(repo, "backend", ".env.local")))
print("backend/.env.example exists:", os.path.exists(os.path.join(repo, "backend", ".env.example")))
import ast
ast.parse(open(os.path.join(repo, "backend", "utils", "config.py"), encoding="utf-8").read())
print("config.py parses OK")
