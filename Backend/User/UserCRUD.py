from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/<user_id>', methods=['GET', 'POST', 'DELETE'])
def user(user_id):
    if request.method == 'GET':
        user = None
        if not user:
            return jsonify({'error': 'user not found'}), 404
        return jsonify(user), 200
    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        return jsonify({'message': 'user created/updated', 'user_id': user_id, 'data': data}), 201
    elif request.method == 'DELETE':
        return jsonify({'message': 'user deleted', 'user_id': user_id}), 204
    return jsonify({'error': 'method not allowed'}), 405