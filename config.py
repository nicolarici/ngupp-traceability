import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey'
    DATABASE = os.path.join(basedir, 'app.sqlite')
    LANGUAGE = 'it_IT'
    BASE_URL = "http://127.0.0.1:5000/"

    with open("app/language/" + LANGUAGE + ".json", "r") as f:
        LABELS = json.load(f)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "static/img"

    # SETUP THE MAIL SERVER

    MAIL_SERVER = "localhost"   # os.environ.get('MAIL_SERVER') or "localhost"
    MAIL_PORT = 1025            # int(os.environ.get('MAIL_PORT')) or 1025

    MAIL_SENDER = "no-replay-tracciabilita@giustizia.it"
    ADMIN_MAIL = "admin.admin@giustizia.it"
