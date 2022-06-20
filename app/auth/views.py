from flask import Blueprint, render_template, request, make_response, session, abort
from sqlalchemy.exc import IntegrityError
from webauthn.helpers.exceptions import InvalidRegistrationResponse
from webauthn.helpers.structs import RegistrationCredential

from auth import security
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
        return render_template(
            "auth/_partials/user_creation_form.html",
            error="That username or email address is already in use. "
            "Please enter a different one.",
        )

    pcco_json = security.prepare_credential_creation(user)
    res = make_response(
        render_template(
            "auth/_partials/register_credential.html",
            public_credential_creation_options=pcco_json,
        )
    )

    session["registration_user_uid"] = user.uid
    return res


@auth.route("/add-credential", methods=["POST"])
def add_credential():
    """Receive a newly registered credentials to validate and save."""
    user_uid = session.get("registration_user_uid")
    if not user_uid:
        abort(make_response("Error user not found", 400))

    registration_credential = RegistrationCredential.parse_raw(request.get_data())
    user = User.query.filter_by(uid=user_uid).first()

    try:
        security.verify_and_save_credential(user, registration_credential)
        session["registration_user_uid"] = None
        return make_response('{"verified": true}', 201)
    except InvalidRegistrationResponse:
        abort(make_response('{"verified": false}', 400))


@auth.route("/login")
def login():
    return "Login user"
