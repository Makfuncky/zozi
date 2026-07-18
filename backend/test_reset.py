import json
import urllib.error
import urllib.request


def main() -> None:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/auth/login/json',
        data=json.dumps({'email': 'admin@zozi.com', 'password': 'admin123'}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        token = json.loads(r.read())['access_token']
    print("Token OK")

    users_req = urllib.request.Request(
        'http://127.0.0.1:8000/admin/users?limit=10',
        headers={'Authorization': 'Bearer ' + token}
    )
    with urllib.request.urlopen(users_req, timeout=5) as r:
        users = json.loads(r.read())

    test_user = next((u for u in users if u['role'] != 'admin'), None)
    if not test_user:
        raise SystemExit("No non-admin user found")

    print("Target:", test_user['id'], test_user['username'])

    reset_req = urllib.request.Request(
        'http://127.0.0.1:8000/admin/users/' + str(test_user['id']) + '/reset-password',
        data=json.dumps({'new_password': 'Test123!'}).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(reset_req, timeout=5) as r:
            print("RESET OK:", json.loads(r.read()))
    except urllib.error.HTTPError as e:
        print("RESET ERROR", e.code, ":", e.read().decode())

    login_req = urllib.request.Request(
        'http://127.0.0.1:8000/auth/login/json',
        data=json.dumps({'email': test_user['email'], 'password': 'Test123!'}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(login_req, timeout=5) as r:
            d = json.loads(r.read())
            print("LOGIN WITH NEW PASSWORD OK: role=" + d['user']['role'])
    except urllib.error.HTTPError as e:
        print("LOGIN FAILED", e.code, ":", e.read().decode())


if __name__ == '__main__':
    main()

