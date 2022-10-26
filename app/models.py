from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from app.extension import db, login
from time import time
import jwt


class User(UserMixin, db.Model):  # type: ignore

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(32), index=True)
    cognome = db.Column(db.String(32), index=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    nome_ufficio = db.Column(db.String(32), index=True)
    ufficio = db.Column(db.String(32), index=True)
    confirmed = db.Column(db.Boolean, default=False)
    superuser=db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Email {}>'.format(self.email)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_registration_token(self, expires_in=600):
        return jwt.encode(
            {'registration': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_registration_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['registration']
        except:
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    try:
        user = User.query.get(int(id))
        if user.confirmed:
            return user
        else:
            return None
    except:
        return None


class Files(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    rg21 = db.Column(db.String(8), index=True)
    rg20 = db.Column(db.String(8), index=True)
    rg16 = db.Column(db.String(8), index=True)
    anno = db.Column(db.String(4), index=True)

    def __repr__(self):
        return f"<File {self.id}>"


class History(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True)
    file_id = db.Column(db.Integer, index=True)
    user_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<History {self.id}>"