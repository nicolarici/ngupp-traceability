from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from app.extension import db, login
from time import time
import jwt
import qrcode


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(32), index=True)
    cognome = db.Column(db.String(32), index=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    nome_ufficio = db.Column(db.String(32), index=True)
    ufficio = db.Column(db.String(32), index=True)
    confirmed = db.Column(db.Boolean, default=False)
    superuser = db.Column(db.Boolean, default=False)

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


class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rg21 = db.Column(db.Integer, index=True)
    rg20 = db.Column(db.Integer, index=True)
    rg16 = db.Column(db.Integer, index=True)
    anno = db.Column(db.Integer, index=True)
    parent = db.Column(db.Integer, default=-1, index=True)

    def __repr__(self):
        return f"<File {self.id}>"

    def __eq__(self, other):
        return self.rg21 == other.rg21 and self.rg20 == other.rg20 and self.rg16 == other.rg16 and self.anno == other.anno

    def generate_qr(self):

        if self.id is None:
            return

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(current_app.config["BASE_URL"] + f"/fascicoli/{self.id}/add")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"app/static/img/QR_{self.id}.png")


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True)
    file_id = db.Column(db.Integer, index=True)
    user_id = db.Column(db.Integer, nullable=False)
    duplicate_from = db.Column(db.Integer, default=-1)

    def __repr__(self):
        return f"<History {self.id}>"