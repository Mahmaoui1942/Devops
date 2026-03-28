from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


users_db = {}


@users_bp.route('', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    user_id = data.get('user_id')
    if user_id in users_db:
        return jsonify({'error': 'user already exists'}), 409
    users_db[user_id] = {'user_id': user_id, 'username': data.get('username'), 'score': 0}
    return jsonify(users_db[user_id]), 201


@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    user = users_db.get(user_id)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    return jsonify(user), 200


@users_bp.route('/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    if user_id not in users_db:
        return jsonify({'error': 'user not found'}), 404
    data = request.get_json()
    users_db[user_id].update(data)
    return jsonify(users_db[user_id]), 200


@users_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    if user_id not in users_db:
        return jsonify({'error': 'user not found'}), 404
    del users_db[user_id]
    return jsonify({'message': 'user deleted'}), 204


@users_bp.route('', methods=['GET'])
def list_users():
    """List all users"""
    return jsonify(list(users_db.values())), 200
