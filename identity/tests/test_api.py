import os
import pytest
import pytest_asyncio
import importlib.util
import jwt
import hashlib

from httpx import AsyncClient


def load_identity_module():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base, "src", "identity.py")
    spec = importlib.util.spec_from_file_location("identity_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeConn:
    def __init__(self, state):
        self.state = state

    async def execute(self, query, *args):
        q = query.lower()
        # domains insert
        if "insert into domains" in q:
            name = args[0]
            if name not in self.state['domains']:
                nid = max(self.state['domains'].values(), default=0) + 1
                self.state['domains'][name] = nid
            return "INSERT 0 1"
        if q.strip().startswith("delete from domains"):
            name = args[0]
            if name in self.state['domains']:
                del self.state['domains'][name]
                return "DELETE 1"
            return "DELETE 0"
        if "insert into users" in q:
            username, password, domain_id = args[0], args[1], args[2]
            uid = max([u['id'] for u in self.state['users']] + [0]) + 1
            self.state['users'].append({'id': uid, 'username': username, 'password': password, 'domain_id': domain_id})
            return "INSERT 0 1"
        if q.strip().startswith("delete from users"):
            uid = args[0]
            for u in list(self.state['users']):
                if u['id'] == uid:
                    self.state['users'].remove(u)
                    return "DELETE 1"
            return "DELETE 0"
        if q.strip().startswith("update users") or "update users set" in q:
            # naive update: match by id
            # handle both update patterns used in identity.py:
            # 1) UPDATE users SET username = COALESCE($1, username), password = $2 WHERE id = $3  -> args: (username, pwd, uid)
            # 2) UPDATE users SET username = COALESCE($1, username) WHERE id = $2 -> args: (username, uid)
            if len(args) == 3:
                username = args[0]
                pwd = args[1]
                uid = args[2]
            elif len(args) == 2:
                username = args[0]
                pwd = None
                uid = args[1]
            else:
                return "UPDATE 0"

            for u in self.state['users']:
                if u['id'] == uid:
                    if username is not None:
                        u['username'] = username
                    if pwd is not None:
                        u['password'] = pwd
                    return "UPDATE 1"
            return "UPDATE 0"
        if q.strip().startswith("delete from user_roles"):
            uid = args[0]
            self.state['user_roles'].pop(uid, None)
            return "DELETE 1"
        if "insert into user_roles" in q:
            uid, rid = args[0], args[1]
            self.state['user_roles'].setdefault(uid, set()).add(rid)
            return "INSERT 0 1"
        if "insert into roles" in q:
            name = args[0]
            if name not in self.state['roles']:
                nid = max(self.state['roles'].values(), default=0) + 1
                self.state['roles'][name] = nid
            return "INSERT 0 1"
        return "OK"

    async def fetchrow(self, query, *args):
        q = query.lower()
        if "select id from domains where name" in q:
            name = args[0]
            if name in self.state['domains']:
                return {'id': self.state['domains'][name]}
            return None
        if "select id from users where username" in q or "select id from users where username = $1" in q:
            username = args[0]
            for u in self.state['users']:
                if u['username'] == username:
                    return {'id': u['id']}
            return None
        if "select id from roles where name" in q:
            name = args[0]
            if name in self.state['roles']:
                return {'id': self.state['roles'][name]}
            return None
        if "select id from users where id =" in q or "where id = $1" in q:
            uid = args[0]
            for u in self.state['users']:
                if u['id'] == uid:
                    return {'id': u['id'], 'username': u['username']}
            return None
        if "select name from domains where id" in q:
            did = args[0]
            for k, v in self.state['domains'].items():
                if v == did:
                    return {'name': k}
            return None
        return None

    async def fetch(self, query, *args):
        q = query.lower()
        if "select id, name from domains" in q:
            return [{'id': v, 'name': k} for k, v in self.state['domains'].items()]
        if "select id, username, domain_id from users" in q or "select id, email, domain_id from users" in q:
            return [{'id': u['id'], 'username': u['username'], 'domain_id': u['domain_id']} for u in self.state['users']]
        if "select roles.name from roles join user_roles" in q:
            uid = args[0]
            rids = self.state['user_roles'].get(uid, set())
            return [{'name': name} for name, rid in self.state['roles'].items() if rid in rids]
        if "select roles.name from roles join user_roles" in q:
            return []
        return []


class FakePool:
    def __init__(self):
        # simple in-memory state
        self.state = {
            'domains': {'example.com': 1},
            'roles': {'user': 1, 'admin': 2},
            'users': [],
            'user_roles': {},
        }
        # seed default admin user (id 1)
        default_admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        default_admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin')
        hashed = hashlib.sha256(default_admin_password.encode()).hexdigest()
        self.state['users'].append({'id': 1, 'username': default_admin_username, 'password': hashed, 'domain_id': 1})
        self.state['user_roles'][1] = {2}

    def acquire(self):
        pool = self

        class _ACtx:
            def __init__(self, state):
                self._conn = FakeConn(state)

            async def __aenter__(self):
                return self._conn

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return _ACtx(self.state)


@pytest.fixture
def identity_module():
    mod = load_identity_module()
    fake = FakePool()

    async def fake_init_db():
        return fake

    # replace the init_db used by startup so the app uses FakePool
    mod.init_db = fake_init_db
    # ensure app has a db_pool for tests (bypass startup)
    mod.app.state.db_pool = fake
    return mod


@pytest_asyncio.fixture
async def client(identity_module):
    # create admin token
    secret = os.getenv('JWT_SECRET', 'b8_XYZ123abc456DEF789ghiJKL0mnoPQ')
    token = jwt.encode({'username': 'admin', 'roles': ['admin']}, secret, algorithm='HS256')
    # httpx 0.28 uses ASGITransport for testing ASGI apps
    from httpx import ASGITransport
    transport = ASGITransport(app=identity_module.app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac, token


@pytest.mark.asyncio
async def test_domain_crud(client):
    ac, token = client
    headers = {'Authorization': f'Bearer {token}'}

    # create domain
    r = await ac.post('/domains', json={'name': 'new.com'}, headers=headers)
    assert r.status_code == 200

    # list domains
    r = await ac.get('/domains', headers=headers)
    assert r.status_code == 200
    names = [d['name'] for d in r.json()]
    assert 'new.com' in names

    # delete domain
    r = await ac.delete('/domains/new.com', headers=headers)
    assert r.status_code == 200

    # list again
    r = await ac.get('/domains', headers=headers)
    names = [d['name'] for d in r.json()]
    assert 'new.com' not in names


@pytest.mark.asyncio
async def test_user_crud(client):
    ac, token = client
    headers = {'Authorization': f'Bearer {token}'}

    # create user
    r = await ac.post('/register', json={'username': 'alice', 'password': 'pw', 'domain': 'example.com', 'roles': ['user']})
    assert r.status_code == 200

    # list users
    r = await ac.get('/users', headers=headers)
    assert r.status_code == 200
    users = r.json()
    assert any(u['username'] == 'alice' for u in users)

    # find alice id
    alice = next(u for u in users if u['username'] == 'alice')
    uid = alice['id']

    # edit user (change username)
    r = await ac.put('/users', json={'id': uid, 'username': 'alice2', 'roles': ['user']}, headers=headers)
    assert r.status_code == 200

    # verify change
    r = await ac.get('/users', headers=headers)
    assert not any(u['username'] == 'alice' for u in r.json())
    assert any(u['username'] == 'alice2' for u in r.json())

    # delete user
    r = await ac.delete(f'/users/{uid}', headers=headers)
    assert r.status_code == 200

    r = await ac.get('/users', headers=headers)
    assert not any(u.get('id') == uid for u in r.json())
