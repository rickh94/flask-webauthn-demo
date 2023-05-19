import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    make_response,
    session,
    abort,
    url_for,
    redirect,
    flash,
)
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse,
)
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential

from auth import security, util
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

    login_user(user)
    session["used_webauthn"] = False

    pcco = security.prepare_credential_creation(user)
    return make_response(
        render_template(
            "auth/_partials/register_credential.html",
            public_credential_creation_options=pcco,
        )
    )


@auth.route("/add-credential", methods=["POST"])
@login_required
def add_credential():
    """Receive a newly registered credentials to validate and save."""
    registration_credential = RegistrationCredential.parse_raw(request.get_data())
    try:
        security.verify_and_save_credential(current_user, registration_credential)
        session["used_webauthn"] = True
        flash("Setup Complete!", "success")

        res = util.make_json_response(
            {"verified": True, "next": url_for("auth.user_profile")}
        )
        res.set_cookie(
            "user_uid",
            current_user.uid,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=datetime.timedelta(days=30),
        )
        return res
    except InvalidRegistrationResponse:
        abort(make_response('{"verified": false}', 400))


@auth.route("/login", methods=["GET"])
def login():
    """Prepare to log in the user with biometric authentication"""
    user_uid = request.cookies.get("user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    # If the user is not remembered from a previous session, we'll need to get
    # their username.
    if not user:
        return render_template("auth/login.html", username=None, auth_options=None)

    # If they are remembered, we can skip directly to biometrics.
    auth_options = security.prepare_login_with_credential(user)

    # Set the user uid on the session to get when we are authenticating
    session["login_user_uid"] = user.uid
    return render_template(
        "auth/login.html", username=user.username, auth_options=auth_options
    )


@auth.route("/prepare-login", methods=["POST"])
def prepare_login():
    """Prepare login options for a user based on their username or email"""
    username_or_email = request.form.get("username_email", "").lower()
    # The lower function just does case insensitivity for our.
    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()

    # if no user matches, send back the form with an error message
    if not user:
        return render_template(
            "auth/_partials/username_form.html", error="No matching user found"
        )

    auth_options = security.prepare_login_with_credential(user)

    res = make_response(
        render_template(
            "auth/_partials/select_login.html",
            auth_options=auth_options,
            username=user.username,
        )
    )

    # set the user uid on the session to get when we are authenticating later.
    session["login_user_uid"] = user.uid
    res.set_cookie(
        "user_uid",
        user.uid,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=datetime.timedelta(days=30),
    )
    return res


@auth.route("/login-switch-user")
def login_switch_user():
    """Remove a remembered user and show the username form again."""
    session.pop("login_user_uid", None)
    res = make_response(redirect(url_for("auth.login")))
    res.delete_cookie("user_uid")
    return res


@auth.route("/verify-login-credential", methods=["POST"])
def verify_login_credential():
    """Log in a user with a submitted credential"""
    user_uid = session.get("login_user_uid")
    user = User.query.filter_by(uid=user_uid).first()
    if not user:
        abort(make_response('{"verified": false}', 400))

    authentication_credential = AuthenticationCredential.parse_raw(request.get_data())
    try:
        security.verify_authentication_credential(user, authentication_credential)
        login_user(user)
        session["used_webauthn"] = True
        flash("Login Complete", "success")

        next_ = request.args.get("next")
        if not next_ or not util.is_safe_url(next_):
            next_ = url_for("auth.user_profile")
        return util.make_json_response({"verified": True, "next": next_})
    except InvalidAuthenticationResponse:
        abort(make_response('{"verified": false}', 400))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("index"))


@auth.route("/user-profile")
@login_required
def user_profile():
    return render_template("auth/user_profile.html")


@auth.route("/email-login")
def email_login():
    """Request login by emailed link."""
    user_uid = session.get("login_user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    # This is probably impossible, but seems like useful protection
    if not user:
        res = make_response(
            render_template(
                "auth/_partials/username_form.html", error="No matching user found."
            )
        )
        session.pop("login_user_uid", None)
        return res
    login_url = security.generate_magic_link(user.uid)
    # TODO: make a template for an html version of the email.
    util.send_email(
        user.email,
        "Flask WebAuthn Login",
        "Click or copy this link to log in. You must use the same browser that "
        f"you were using when you requested to log in. {login_url}",
        render_template(
            "auth/email/login_email.html", username=user.username, login_url=login_url
        ),
    )
    res = make_response(render_template("auth/_partials/email_login_message.html"))
    res.set_cookie(
        "magic_link_user_uid",
        user.uid,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=datetime.timedelta(minutes=15),
    )
    return res


@auth.route("/magic-link")
def magic_link():
    """Handle incoming magic link authentications."""
    url_secret = request.args.get("secret")
    user_uid = request.cookies.get("magic_link_user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    if not user:
        flash("Could not log in. Please try again", "failure")
        return redirect(url_for("auth.login"))

    if security.verify_magic_link(user_uid, url_secret):
        login_user(user)
        session["used_webauthn"] = False
        flash("Logged in", "success")
        return redirect(url_for("auth.user_profile"))

    return redirect(url_for("auth.login"))


@auth.route("/create-credential")
@login_required
def create_credential():
    """Start creation of new credentials by existing users."""
    pcco = security.prepare_credential_creation(current_user)
    # flash("Click the button to start setup", "warning")
    return make_response(
        render_template(
            "auth/_partials/register_credential.html",
            public_credential_creation_options=pcco,
        )
    )

    # TODO: create a route to revoke all credentials
