from flask import Blueprint, request, jsonify
from datetime import datetime

games_bp = Blueprint('games', __name__, url_prefix='/games')


games_db = {}

@games_bp.route('', methods=['POST'])
def create_game():
    """Create a new game"""
    data = request.get_json()
    game_id = data.get('game_id')
    if game_id in games_db:
        return jsonify({'error': 'game already exists'}), 409
    
    game = {
        'game_id': game_id,
        'title': data.get('title'),
        'width': data.get('width', 100),
        'height': data.get('height', 100),
        'players': data.get('players', []),
        'grid': [[0 for _ in range(data.get('width', 100))] for _ in range(data.get('height', 100))],
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }
    games_db[game_id] = game
    return jsonify(game), 201

@games_bp.route('/<game_id>', methods=['GET'])
def get_game(game_id):

    game = games_db.get(game_id)
    if not game:
        return jsonify({'error': 'game not found'}), 404
    return jsonify(game), 200

@games_bp.route('/<game_id>/pixel', methods=['POST'])
def place_pixel(game_id):

    if game_id not in games_db:
        return jsonify({'error': 'game not found'}), 404
    
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    color = data.get('color')
    user_id = data.get('user_id')
    
    game = games_db[game_id]
    if x < 0 or x >= game['width'] or y < 0 or y >= game['height']:
        return jsonify({'error': 'pixel out of bounds'}), 400
    
    game['grid'][y][x] = color
    return jsonify({'message': 'pixel placed', 'x': x, 'y': y, 'color': color}), 200

@games_bp.route('/<game_id>/grid', methods=['GET'])
def get_grid(game_id):

    if game_id not in games_db:
        return jsonify({'error': 'game not found'}), 404
    return jsonify(games_db[game_id]['grid']), 200

@games_bp.route('', methods=['GET'])
def list_games():

    return jsonify(list(games_db.values())), 200

@games_bp.route('/<game_id>', methods=['DELETE'])
def delete_game(game_id):

    if game_id not in games_db:
        return jsonify({'error': 'game not found'}), 404
    del games_db[game_id]
    return jsonify({'message': 'game deleted'}), 204