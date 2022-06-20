import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User
from auth.views import auth

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "auth.login"

db.init_app(app)
Migrate(app, db)

app.register_blueprint(auth, url_prefix="/auth")


@login_manager.user_loader
def load_user(user_uid):
    return User.query.filter_by(uid=user_uid).first()


@app.route("/")
def index():
    """The main homepage. This is a stub since it's a demo project."""
    return render_template("index.html")
