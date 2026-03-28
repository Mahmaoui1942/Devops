import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app  # noqa: E402
import Game.GameCRUD as game_module  # noqa: E402


@pytest.fixture(autouse=True)
def clear_games():
    game_module.games_memory.clear()
    yield
    game_module.games_memory.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_create_game(client):
    resp = client.post('/api/games', json={'game_id': 'g1', 'title': 'Test', 'width': 5, 'height': 5})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['game_id'] == 'g1'
    assert data['width'] == 5
    assert data['height'] == 5
    assert data['status'] == 'active'
    assert len(data['grid']) == 5
    assert len(data['grid'][0]) == 5


def test_create_game_missing_id(client):
    resp = client.post('/api/games', json={'title': 'No ID'})
    assert resp.status_code == 400


def test_create_game_duplicate(client):
    client.post('/api/games', json={'game_id': 'g2', 'width': 3, 'height': 3})
    resp = client.post('/api/games', json={'game_id': 'g2', 'width': 3, 'height': 3})
    assert resp.status_code == 409


def test_get_game(client):
    client.post('/api/games', json={'game_id': 'g3', 'title': 'Arena', 'width': 4, 'height': 4})
    resp = client.get('/api/games/g3')
    assert resp.status_code == 200
    assert resp.get_json()['game_id'] == 'g3'


def test_get_game_not_found(client):
    resp = client.get('/api/games/unknown')
    assert resp.status_code == 404


def test_list_games(client):
    client.post('/api/games', json={'game_id': 'g4', 'width': 2, 'height': 2})
    client.post('/api/games', json={'game_id': 'g5', 'width': 2, 'height': 2})
    resp = client.get('/api/games')
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_place_pixel(client):
    client.post('/api/games', json={'game_id': 'g6', 'width': 5, 'height': 5})
    resp = client.post('/api/games/g6/pixel', json={'x': 1, 'y': 2, 'color': 3})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['x'] == 1
    assert data['y'] == 2
    assert data['color'] == 3


def test_place_pixel_missing_fields(client):
    client.post('/api/games', json={'game_id': 'g7', 'width': 5, 'height': 5})
    resp = client.post('/api/games/g7/pixel', json={'x': 1})
    assert resp.status_code == 400


def test_place_pixel_out_of_bounds(client):
    client.post('/api/games', json={'game_id': 'g8', 'width': 3, 'height': 3})
    resp = client.post('/api/games/g8/pixel', json={'x': 5, 'y': 0, 'color': 1})
    assert resp.status_code == 400


def test_place_pixel_game_not_found(client):
    resp = client.post('/api/games/unknown/pixel', json={'x': 0, 'y': 0, 'color': 1})
    assert resp.status_code == 404


def test_get_grid(client):
    client.post('/api/games', json={'game_id': 'g9', 'width': 3, 'height': 3})
    client.post('/api/games/g9/pixel', json={'x': 0, 'y': 0, 'color': 7})
    resp = client.get('/api/games/g9/grid')
    assert resp.status_code == 200
    grid = resp.get_json()
    assert grid[0][0] == 7


def test_get_grid_not_found(client):
    resp = client.get('/api/games/unknown/grid')
    assert resp.status_code == 404


def test_delete_game(client):
    client.post('/api/games', json={'game_id': 'g10', 'width': 2, 'height': 2})
    resp = client.delete('/api/games/g10')
    assert resp.status_code == 200
    assert client.get('/api/games/g10').status_code == 404
