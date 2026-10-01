from infrastructure.database.database import engine
from infrastructure.utils.auth import verify_password
from sqlalchemy import text

with open("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/_verify_out.txt", "w") as f:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT email, hashed_password FROM accounts.users"))
        rows = res.fetchall()
        f.write(f"rows={len(rows)}\n")
        for r in rows:
            email, hp = r.email, r.hashed_password
            ok = verify_password("DevSeed123!", hp)
            f.write(f"{email}: hash prefix {hp[:20]!r} verify={ok}\n")
        f.write("DONE\n")