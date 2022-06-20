import os

from flask import Flask, render_template
from flask_migrate import Migrate

from models import db
from auth.views import auth

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)
Migrate(app, db)

app.register_blueprint(auth, url_prefix='/auth')


@app.route("/")
def index():
    """The main homepage. This is a stub since it's a demo project."""
    return render_template("index.html")
