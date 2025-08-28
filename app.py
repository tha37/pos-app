from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from models import User
from routes import *

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_db_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_db_tables()
    app.run(host='0.0.0.0', port=5000)