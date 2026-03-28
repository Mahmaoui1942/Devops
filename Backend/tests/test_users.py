import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app  # noqa: E402
import User.UserCRUD as user_module  # noqa: E402


@pytest.fixture(autouse=True)
def clear_users():
    user_module.users_db.clear()
    yield
    user_module.users_db.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_create_user(client):
    resp = client.post('/api/users', json={'user_id': 'u1', 'username': 'alice'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['user_id'] == 'u1'
    assert data['username'] == 'alice'
    assert data['score'] == 0


def test_create_user_duplicate(client):
    client.post('/api/users', json={'user_id': 'u1', 'username': 'alice'})
    resp = client.post('/api/users', json={'user_id': 'u1', 'username': 'alice'})
    assert resp.status_code == 409


def test_get_user(client):
    client.post('/api/users', json={'user_id': 'u2', 'username': 'bob'})
    resp = client.get('/api/users/u2')
    assert resp.status_code == 200
    assert resp.get_json()['username'] == 'bob'


def test_get_user_not_found(client):
    resp = client.get('/api/users/unknown')
    assert resp.status_code == 404


def test_update_user(client):
    client.post('/api/users', json={'user_id': 'u3', 'username': 'carol'})
    resp = client.put('/api/users/u3', json={'score': 10})
    assert resp.status_code == 200
    assert resp.get_json()['score'] == 10


def test_update_user_not_found(client):
    resp = client.put('/api/users/unknown', json={'score': 5})
    assert resp.status_code == 404


def test_delete_user(client):
    client.post('/api/users', json={'user_id': 'u4', 'username': 'dave'})
    resp = client.delete('/api/users/u4')
    assert resp.status_code == 204
    assert client.get('/api/users/u4').status_code == 404


def test_delete_user_not_found(client):
    resp = client.delete('/api/users/unknown')
    assert resp.status_code == 404


def test_list_users(client):
    client.post('/api/users', json={'user_id': 'u5', 'username': 'eve'})
    client.post('/api/users', json={'user_id': 'u6', 'username': 'frank'})
    resp = client.get('/api/users')
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
