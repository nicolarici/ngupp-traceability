from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extension import db, login


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(32), index=True)
    cognome = db.Column(db.String(32), index=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    ufficio = db.Column(db.String(32), index=True)

    def __repr__(self):
        return '<Email {}>'.format(self.email)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), index=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name =  db.Column(db.String(64), index=True)
    user_office = db.Column(db.String(64), index=True)

    def __repr__(self):
        return '<File {}>'.format(self.code)