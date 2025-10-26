import os
import subprocess
import time
import shutil
import pytest
from httpx import Client


COMPOSE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml'))
def get_service_url(service, port, default_host='localhost'):
    """Get service URL, preferring Docker service names in containerized environment"""
    if os.getenv('SKIP_COMPOSE') == '1':  # Running in Docker test container
        return f'http://{service}:{port}'
    return f'http://{default_host}:{port}'

BASE_URL = get_service_url('identity', 8001)


def docker_compose_up(services):
    # When running inside the test container there's no Docker binary available.
    # In that case the outer Makefile/compose already started required services,
    # so just skip trying to run docker here.
    if shutil.which('docker') is None or os.environ.get('SKIP_COMPOSE'):
        print('docker not available in container or SKIP_COMPOSE set; skipping docker_compose_up')
        return
    cmd = ['docker', 'compose', '-f', COMPOSE, 'up', '-d'] + services
    subprocess.check_call(cmd)


def docker_compose_down():
    if shutil.which('docker') is None or os.environ.get('SKIP_COMPOSE'):
        print('docker not available in container or SKIP_COMPOSE set; skipping docker_compose_down')
        return
    cmd = ['docker', 'compose', '-f', COMPOSE, 'down', '--volumes', '--remove-orphans']
    subprocess.check_call(cmd)


def wait_for_identity(timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with Client(timeout=5) as c:
                r = c.get(BASE_URL + '/docs')
                if r.status_code == 200:
                    return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError('identity service did not become ready in time')


@pytest.fixture(scope='module')
def compose_env():
    # start minimal services required: postgres and identity
    docker_compose_up(['postgres'])
    try:
        # now start identity (depends on postgres health)
        docker_compose_up(['identity'])
        wait_for_identity(timeout=120)
        yield
    finally:
        docker_compose_down()


def get_admin_token():
    # default seeded admin credentials
    with Client() as c:
        r = c.post(BASE_URL + '/login', json={'username': 'admin', 'password': 'admin'})
        r.raise_for_status()
        return r.json()['access_token']


def test_domain_crud_integration(compose_env):
    token = get_admin_token()
    headers = {'Authorization': f'Bearer {token}'}

    with Client() as c:
        # create
        r = c.post(BASE_URL + '/domains', json={'name': 'itesting.local'}, headers=headers)
        assert r.status_code == 200

        # list
        r = c.get(BASE_URL + '/domains', headers=headers)
        assert r.status_code == 200
        names = [d['name'] for d in r.json()]
        assert 'itesting.local' in names

        # delete
        r = c.delete(BASE_URL + '/domains/itesting.local', headers=headers)
        assert r.status_code == 200

        r = c.get(BASE_URL + '/domains', headers=headers)
        names = [d['name'] for d in r.json()]
        assert 'itesting.local' not in names


def test_user_crud_integration(compose_env):
    token = get_admin_token()
    headers = {'Authorization': f'Bearer {token}'}

    with Client() as c:
        # register user
        r = c.post(BASE_URL + '/register', json={'username': 'bob', 'password': 'secret', 'domain': 'example.com', 'roles': ['user']})
        assert r.status_code == 200

        # list users
        r = c.get(BASE_URL + '/users', headers=headers)
        assert r.status_code == 200
        users = r.json()
        bob = next((u for u in users if u['username'] == 'bob'), None)
        assert bob is not None
        uid = bob['id']

        # edit user - change username but don't send password (should preserve password)
        r = c.put(BASE_URL + '/users', json={'id': uid, 'username': 'bob2', 'roles': ['user']}, headers=headers)
        assert r.status_code == 200

        # verify changed
        r = c.get(BASE_URL + '/users', headers=headers)
        assert not any(u['username'] == 'bob' for u in r.json())
        assert any(u['username'] == 'bob2' for u in r.json())

        # delete user
        r = c.delete(f"{BASE_URL}/users/{uid}", headers=headers)
        assert r.status_code == 200

        r = c.get(BASE_URL + '/users', headers=headers)
        assert not any(u.get('id') == uid for u in r.json())
