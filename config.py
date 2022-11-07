import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'devkey'
    DATABASE = os.path.join(basedir, 'app.db')
    LANGUAGE = 'it_IT'
    BASE_URL = "http://127.0.0.1:5000/"

    BOOTSTRAP_USE_MINIFIED = True
    BOOTSTRAP_CDN_FORCE_SSL = True

    BOOTSTRAP_VERSION = "5.2.2"
    JQUERY_VERSION = "2.1.1"
    POPPER_VERSION = "2.9.2"

    with open("app/static/language/" + LANGUAGE + ".json", "r") as f:
        LABELS = json.load(f)

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "static/img"

    # SETUP THE MAIL SERVER

    MAIL_SERVER = "localhost"   # os.environ.get('MAIL_SERVER') or "localhost"
    MAIL_PORT = 1025            # int(os.environ.get('MAIL_PORT')) or 1025

    MAIL_SENDER = "no-replay-tracciabilita@giustizia.it"
    ADMIN_MAIL = "presidente.tribunale.brescia@giustizia.it"
