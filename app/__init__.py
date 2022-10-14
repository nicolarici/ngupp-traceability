from ensurepip import bootstrap
from flask import Flask, render_template, request
from app.models import Files, User
from config import Config
from flask_login import login_required
from flask_bootstrap import Bootstrap
import os

"""
    Create and configure the app.
"""

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    bootstrap = Bootstrap(app)

    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads):
        os.makedirs(uploads)
    
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
                               title=app.config["LABELS"]["home_title"])
    
    @app.route('/api/data')
    @login_required
    def data():
        query = Files.query.join(User, User.id==Files.user_id).add_columns(User.nome, User.cognome, User.ufficio, Files.code, Files.created)
        
        # search filter
        search = request.args.get('search[value]')
        if search:
            query = query.filter(db.or_(
                Files.code.like(f'%{search}%'),
            ))
        total_filtered = query.count()

        # sorting
        order = []
        i = 0
        while True:
            col_index = request.args.get(f'order[{i}][column]')
            if col_index is None:
                break
            col_code = request.args.get(f'columns[{col_index}][data]')
            if col_code not in "code":
                col_code = 'code'
            descending = request.args.get(f'order[{i}][dir]') == 'desc'
            col = getattr(Files, col_code)
            if descending:
                col = col.desc()
            order.append(col)
            i += 1
        if order:
            query = query.order_by(*order)

        # pagination
        start = request.args.get('start', type=int)
        length = request.args.get('length', type=int)
        query = query.offset(start).limit(length)


        def render_file(file):
            return {
                'code': file.code,
                'user_name': file.nome + ' ' + file.cognome,
                'user_office': file.ufficio,
                'created': file.created.strftime(' %d/%m/%Y %H:%M ')
            }

        # response
        return {
            'data': [render_file(file) for file in query],
            'recordsFiltered': total_filtered,
            'recordsTotal': Files.query.count(),
            'draw': request.args.get('draw', type=int),
        }




    # Aggiunge le blueprint

    from . import auth
    app.register_blueprint(auth.bp)

    from . import user
    app.register_blueprint(user.bp)
    
    from . import fascicoli
    app.register_blueprint(fascicoli.bp)


    return app
