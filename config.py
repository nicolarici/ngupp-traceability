import os
import json 

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey'
    LANGUAGE = 'it_IT'

    with open("app/language/it_IT.json", "r") as f:
        LABELS = json.load(f)