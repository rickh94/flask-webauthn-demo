from flask import Blueprint, render_template, request, make_response
from sqlalchemy.exc import IntegrityError

from models import User, db

auth = Blueprint("auth", __name__, template_folder="templates")


@auth.route("/register")
def register():
    """Show the form for new users to register"""
    return render_template("auth/register.html")


@auth.route("/create-user", methods=["POST"])
def create_user():
    """Handle creation of new users from the user creation form."""
    name = request.form.get("name")
    username = request.form.get("username")
    email = request.form.get("email")

    user = User(name=name, username=username, email=email)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        return make_response("Invalid form data", 400)

    return make_response("User Created", 201)


@auth.route("/login")
def login():
    return "Login user"
