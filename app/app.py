import os
import uuid

from flask import Flask, render_template, flash
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User
from auth.views import auth

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_FROM"] = os.getenv("MAIL_FROM")

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "auth.login"

db.init_app(app)
Migrate(app, db)

app.register_blueprint(auth, url_prefix="/auth")


@login_manager.user_loader
def load_user(user_uid):
    return User.query.filter_by(uid=user_uid).first()


@app.context_processor
def utility_processor():
    def random_id():
        return uuid.uuid4().hex

    return dict(random_id=random_id)


@app.route("/")
def index():
    """The main homepage. This is a stub since it's a demo project."""
    return render_template("index.html")
