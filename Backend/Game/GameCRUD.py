from flask import Blueprint, request, jsonify
from datetime import datetime
import psycopg2
import psycopg2.extras
import os
import json

games_bp = Blueprint('games', __name__, url_prefix='/api/games')
games_memory = {}


def get_db():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        dbname=os.environ.get('DB_NAME', 'pixelwar'),
        user=os.environ.get('DB_USER', 'pixelwar'),
        password=os.environ.get('DB_PASSWORD', 'pixelwar'),
    )


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            title TEXT,
            width INT,
            height INT,
            grid JSONB,
            status TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


try:
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")


@games_bp.route('', methods=['POST'])
def create_game():
    data = request.get_json() or {}
    game_id = data.get('game_id')
    if not game_id:
        return jsonify({'error': 'game_id is required'}), 400
    width = data.get('width', 50)
    height = data.get('height', 50)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    now = datetime.now().isoformat()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO games (game_id, title, width, height, grid, status, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (game_id, data.get('title'), width, height, json.dumps(grid), 'active', datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'game already exists'}), 409
    except Exception:
        if game_id in games_memory:
            return jsonify({'error': 'game already exists'}), 409
        games_memory[game_id] = {
            'game_id': game_id,
            'title': data.get('title'),
            'width': width,
            'height': height,
            'grid': grid,
            'status': 'active',
            'created_at': now,
        }
    return jsonify({'game_id': game_id, 'width': width, 'height': height, 'grid': grid, 'status': 'active'}), 201


@games_bp.route('/<game_id>', methods=['GET'])
def get_game(game_id):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({'error': 'game not found'}), 404
        return jsonify(dict(row)), 200
    except Exception:
        row = games_memory.get(game_id)
        if not row:
            return jsonify({'error': 'game not found'}), 404
        return jsonify(row), 200


@games_bp.route('/<game_id>/pixel', methods=['POST'])
def place_pixel(game_id):
    data = request.get_json() or {}
    x = data.get('x')
    y = data.get('y')
    color = data.get('color')
    if x is None or y is None or color is None:
        return jsonify({'error': 'x, y and color are required'}), 400
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT width, height FROM games WHERE game_id = %s", (game_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({'error': 'game not found'}), 404
        if x < 0 or x >= row['width'] or y < 0 or y >= row['height']:
            cur.close()
            conn.close()
            return jsonify({'error': 'pixel out of bounds'}), 400
        cur.execute(
            """
            UPDATE games
            SET grid = jsonb_set(grid, ARRAY[%s, %s]::text[], to_jsonb(%s::int), false)
            WHERE game_id = %s
            """,
            (y, x, color, game_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'pixel placed', 'x': x, 'y': y, 'color': color}), 200
    except Exception:
        row = games_memory.get(game_id)
        if not row:
            return jsonify({'error': 'game not found'}), 404
        if x < 0 or x >= row['width'] or y < 0 or y >= row['height']:
            return jsonify({'error': 'pixel out of bounds'}), 400
        row['grid'][y][x] = color
        return jsonify({'message': 'pixel placed', 'x': x, 'y': y, 'color': color}), 200


@games_bp.route('/<game_id>/grid', methods=['GET'])
def get_grid(game_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT grid FROM games WHERE game_id = %s", (game_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({'error': 'game not found'}), 404
        return jsonify(row[0]), 200
    except Exception:
        row = games_memory.get(game_id)
        if not row:
            return jsonify({'error': 'game not found'}), 404
        return jsonify(row['grid']), 200


@games_bp.route('', methods=['GET'])
def list_games():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT game_id, title, width, height, status, created_at FROM games")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception:
        rows = []
        for game in games_memory.values():
            rows.append({
                'game_id': game['game_id'],
                'title': game['title'],
                'width': game['width'],
                'height': game['height'],
                'status': game['status'],
                'created_at': game['created_at'],
            })
        return jsonify(rows), 200


@games_bp.route('/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM games WHERE game_id = %s", (game_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'game deleted'}), 200
    except Exception:
        games_memory.pop(game_id, None)
        return jsonify({'message': 'game deleted'}), 200
