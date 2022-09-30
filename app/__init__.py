from flask import Flask, render_template
from config import Config
import locale

"""
    Create and configure the app.
"""

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)


    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index.html', 
                               title=app.config["LABELS"]["home_title"], 
                               home_text=app.config["LABELS"]["home_text"])


    # Aggiunge la blueprint per l'autenticazione

    from . import auth
    app.register_blueprint(auth.bp)


    return app
