from flask import Flask
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from User.UserCRUD import users_bp
from Game.GameCRUD import games_bp

app = Flask(__name__)
CORS(app)
metrics = PrometheusMetrics(app)


@app.route('/')
def home():
    return {"message": "pixelWar Backend API", "version": "1.0"}


app.register_blueprint(users_bp)
app.register_blueprint(games_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
