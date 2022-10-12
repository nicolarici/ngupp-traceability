from msilib.schema import File
from flask import Flask, render_template, request
from app.models import Files
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
        files = Files.query.order_by(Files.created).all()
        return render_template('index.html', 
                               title=app.config["LABELS"]["home_title"], 
                               home_text=app.config["LABELS"]["home_text"], files = files)
    
    @app.route('/api/data')
    @login_required
    def data():
        query = Files.query

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

        # response
        return {
            'data': [file.to_dict() for file in query],
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
