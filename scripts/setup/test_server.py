"""Quick smoke test of the running backend server."""
import urllib.request
import urllib.error
import json
import sqlite3
import os

BASE = "http://127.0.0.1:9000"

def get(path):
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        body = r.read().decode()
        return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.reason
    except Exception as e:
        return 0, str(e)


def main() -> None:
    code, body = get("/health")
    print(f"GET /health -> {code}: {body[:120]}")

    code, body = get("/docs")
    print(f"GET /docs -> {code}: ({len(body)} bytes)")

    code, body = get("/openapi.json")
    if code == 200:
        schema = json.loads(body)
        paths = list(schema.get("paths", {}).keys())
        print(f"GET /openapi.json -> {code}: {len(paths)} paths")
        for path in paths[:15]:
            print(f"  {path}")
        if len(paths) > 15:
            print(f"  ... and {len(paths)-15} more")
    else:
        print(f"GET /openapi.json -> {code}: {body[:120]}")

    code, body = get("/api/v1/products/")
    print(f"GET /api/v1/products/ -> {code}: {body[:200]}")

    code, body = get("/api/v1/categories/")
    print(f"GET /api/v1/categories/ -> {code}: {body[:200]}")

    try:
        data = json.dumps({"email": "test@test.com", "password": "Test1234!", "full_name": "Test User"}).encode()
        req = urllib.request.Request(f"{BASE}/api/v1/auth/register", data=data, headers={"Content-Type": "application/json"})
        response = urllib.request.urlopen(req)
        print(f"POST /api/v1/auth/register -> {response.status}: {response.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"POST /api/v1/auth/register -> {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"POST /api/v1/auth/register -> ERROR: {e}")

    try:
        data = json.dumps({"email": "test@test.com", "password": "Test1234!"}).encode()
        req = urllib.request.Request(f"{BASE}/api/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
        response = urllib.request.urlopen(req)
        print(f"POST /api/v1/auth/login -> {response.status}: {response.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"POST /api/v1/auth/login -> {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"POST /api/v1/auth/login -> ERROR: {e}")

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "zozi.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"\n=== Database: {os.path.getsize(db_path):,} bytes, {len(tables)} tables ===")
        for table in sorted(tables):
            count = conn.execute(f'SELECT COUNT(*) FROM "{table[0]}"').fetchone()[0]
            print(f"  {table[0]}: {count} rows")
        conn.close()
    else:
        print(f"\nDB not found at {db_path}")


if __name__ == "__main__":
    main()
