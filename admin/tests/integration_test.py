import requests
import sys

ADMIN_URL = "http://localhost:8005"


def api_login(email, password):
    r = requests.post(f"{ADMIN_URL}/api/login", json={"email": email, "password": password})
    return r


def manage_user(token, username, domain="example.com", role="user", password="TempPass1!"):
    data = {
        'username': username,
        'domain': domain,
        'role': role,
        'password': password,
        'token': token
    }
    r = requests.post(f"{ADMIN_URL}/manage-user", data=data)
    return r


if __name__ == '__main__':
    # Use seeded admin creds
    login_resp = api_login('admin@example.com', 'admin')
    print('login:', login_resp.status_code, login_resp.text)
    if login_resp.status_code != 200:
        print('Login failed, aborting')
        sys.exit(2)
    token = login_resp.json().get('access_token')
    # create user
    r1 = manage_user(token, 'itestuser')
    print('create1:', r1.status_code, r1.text)
    # duplicate create should be 400
    r2 = manage_user(token, 'itestuser')
    print('create2 (dup):', r2.status_code, r2.text)
    if r2.status_code == 400:
        print('SUCCESS: duplicate user returned 400 as expected')
        sys.exit(0)
    else:
        print('FAIL: duplicate user did not return 400')
        sys.exit(1)
