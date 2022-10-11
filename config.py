import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey'
    DATABASE = os.path.join(basedir, 'app.sqlite')
    LANGUAGE = 'it_IT'
    BASE_URL="http://127.0.0.1:5000/" #TODO: cambia con indirizzo in deploy

    with open("app/language/" + LANGUAGE + ".json", "r") as f:
        LABELS = json.load(f)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False