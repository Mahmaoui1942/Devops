from flask import Flask
from User.UserCRUD import users_bp


app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, world!"

app.register_blueprint(users_bp)

app.run(port=5000)


