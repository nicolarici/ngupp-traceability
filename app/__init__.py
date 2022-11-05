from flask import Flask, render_template, request
from app.models import Files, History, User
from config import Config
from flask_login import login_required
from flask_bootstrap import WebCDN
import os


"""
    Create and configure the app.
"""

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads):
        os.makedirs(uploads)
    
    # Set-up estensioni.
    
    from app.extension import login
    login.init_app(app)
    login.login_view = 'auth.login'
    login.login_message = app.config["LABELS"]["login_required"]
    login.login_message_category = "danger"


    from app.extension import db
    db.init_app(app)

    initialize_db(app, db)
    
    from app.extension import migrate
    migrate.init_app(app)

    from app.extension import mail
    mail.init_app(app)

    from app.extension import bootstrap
    bootstrap.init_app(app)
    app.extensions['bootstrap']['cdns']['jquery'] = WebCDN("//cdnjs.cloudflare.com/ajax/libs/jquery/" + app.config["JQUERY_VERSION" ] + "/")
    app.extensions['bootstrap']['cdns']['bootstrap'] = WebCDN("//cdn.jsdelivr.net/npm/bootstrap@" + app.config["BOOTSTRAP_VERSION" ] + "/dist/")
    app.extensions['bootstrap']['cdns']['popper'] = WebCDN("//cdn.jsdelivr.net/npm/@popperjs/core@" + app.config["POPPER_VERSION" ] + "/dist/")


    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return render_template('index.html')
    
    @app.route('/api/data')
    @login_required
    def data():
        query = db.session.query(User, History, Files).filter(User.id == History.user_id).filter(History.file_id == Files.id).add_columns(User.nome, User.cognome, User.nome_ufficio, User.ufficio, Files.id, Files.rg16, Files.rg20, Files.rg21, Files.anno, History.created)
        
        # search filter
        search = request.args.get('search[value]')
        if search:
            query = query.filter(db.or_(
                User.nome.like(f'%{search}%'),
                User.cognome.like(f'%{search}%'),
                User.nome_ufficio.like(f'%{search}%'),
                User.ufficio.like(f'%{search}%'),
                Files.rg16.like(f'%{search}%'),
                Files.rg20.like(f'%{search}%'),
                Files.rg21.like(f'%{search}%'),
                Files.anno.like(f'%{search}%')
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
                'file_id': file.id,
                'RG16': file.rg16,
                'RG20': file.rg20,
                'RG21': file.rg21,
                'anno': file.anno,
                'user_name': file.nome + ' ' + file.cognome,
                'office_name': file.nome_ufficio,
                'office_number': file.ufficio,
                'created': file.created.strftime(' %H:%M - %d/%m/%Y '),
                'btn': '<div class="d-grid gap-2"><a class="btn btn-sm btn-success" href="fascicoli/' + str(file.id) + '" role="button">' + app.config["LABELS"]["apri"] + '</a></div>'

            }
    
        distinct_files = {}
        for file in query:
            if file.id not in distinct_files:
                distinct_files[file.id] = render_file(file)

        # response
        return {
            'data': list(distinct_files.values()),
            #'data': [render_file(file) for file in query],
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
    
    from . import statistics
    app.register_blueprint(statistics.bp)
    
    return app


def initialize_db(app, db):
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            db.create_all()
            db.session.commit()

        # Rimuove immagini rimaste nella cartella per sbaglio

        uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])

        for file in os.listdir(uploads):
            os.remove(os.path.join(uploads, file))
