from flask import Flask, render_template
from config import Config
from flask_login import login_required


"""
    Create and configure the app.
"""

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    # Set-up estensioni.
    
    from app.extension import login
    login.init_app(app)
    login.login_view = 'auth.login'
    login.login_message = app.config["LABELS"]["login_required"]


    from app.extension import db
    db.init_app(app)
    
    from app.extension import migrate
    migrate.init_app(app)


    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return render_template('index.html', 
                               title=app.config["LABELS"]["home_title"], 
                               home_text=app.config["LABELS"]["home_text"])


    # Aggiunge le blueprint

    from . import auth
    app.register_blueprint(auth.bp)

    from . import user
    app.register_blueprint(user.bp)


    return app
