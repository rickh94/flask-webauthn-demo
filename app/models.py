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


class WebAuthnCredential(db.Model):
    """Stored WebAuthn Credentials as a replacement for passwords."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    credential_id = db.Column(db.LargeBinary, nullable=False)
    credential_public_key = db.Column(db.LargeBinary, nullable=False)
    current_sign_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Credential {self.credential_id}>"
