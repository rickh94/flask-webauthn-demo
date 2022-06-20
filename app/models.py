import uuid

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()


def _str_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    """A user in the database"""

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(40), default=_str_uuid, unique=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    credentials = db.relationship(
        "WebAuthnCredential",
        backref=backref("user", cascade="all, delete"),
        lazy=True,
    )

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def is_authenticated(self):
        """If we can access this user model from current user, they are authenticated,
        so this always returns True."""
        return True

    @property
    def is_anonymous(self):
        """An actual user is never anonymous. Always returns False."""
        return False

    @property
    def is_active(self):
        """Returns True for all users for simplicity. This would need to be a column
        in the database in order to deactivate users."""
        return True

    def get_id(self):
        """Returns the user id. We're using the generated uuid rather than the database
        primary key."""
        return self.uid


class WebAuthnCredential(db.Model):
    """Stored WebAuthn Credentials as a replacement for passwords."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    credential_id = db.Column(db.LargeBinary, nullable=False)
    credential_public_key = db.Column(db.LargeBinary, nullable=False)
    current_sign_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Credential {self.credential_id}>"
