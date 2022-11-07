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
                'created': file.created.timestamp(),
                'btn': '<div class="d-grid gap-2"><a class="btn btn-sm btn-success" href="fascicoli/' + str(file.id) + '" role="button">' + app.config["LABELS"]["apri"] + '</a></div>'

            }
    
        distinct_files = {}
        for file in query:
            if file.id not in distinct_files:
                distinct_files[file.id] = render_file(file)

        # response
        return {
            'data': list(distinct_files.values()),
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


from datetime import datetime

def initialize_db(app, db):

    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):

            # Rimuove immagini rimaste nella cartella per sbaglio

            uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])

            for file in os.listdir(uploads):
                os.remove(os.path.join(uploads, file))

            # Creazione tabelle

            db.create_all()
            db.session.commit()

            # Cancelleria

            u1 = User(nome="Emanuela", cognome="Rizzi", nome_ufficio="Cancelleria GIP/GUP", ufficio="1.58", email="emanuela.rizzi@giustizia.it", confirmed=1)
            u1.set_password("qwertyuiop1")

            u5 = User(nome="Laura", cognome="Talenti", nome_ufficio="Cancelleria GIP/GUP", ufficio="1.58", email="laura.talenti@giustizia.it", confirmed=1)
            u5.set_password("qwertyuiop1")

            u6 = User(nome="Emilia", cognome="Del Bono", nome_ufficio="Cancelleria GIP/GUP", ufficio="1.58", email="emilia.delbono@giustizia.it", confirmed=1)
            u6.set_password("qwertyuiop1")

            u7 = User(nome="Roberto", cognome="Martinazzoli", nome_ufficio="Cancelleria GIP/GUP", ufficio="1.58", email="roberto.martinazzoli@giustizia.it", confirmed=1)
            u7.set_password("qwertyuiop1")

            # Giudice

            u2 = User(nome="Federica", cognome="Brugnara", nome_ufficio="Ufficio Giudice GIP/GUP", ufficio="1.28", email="federica.brugnara@giustizia.it", confirmed=1)
            u2.set_password("qwertyuiop1")

            # Magistrato capo
 
            u3 = User(nome="Carlo", cognome="Bianchetti", nome_ufficio="Ufficio Magistrato Cordinatore", ufficio="2.55", email="carlo.bianchetti@giustizia.it", confirmed=1, superuser=1)
            u3.set_password("qwertyuiop1")

            # Presidente superadmin

            u4 = User(nome="Presidente", cognome="Tribunale", nome_ufficio="Presidenza", ufficio="4.80", email="presidente.tribunale.brescia@giustizia.it", confirmed=1, superuser=1)
            u4.set_password("qwertyuiop1")

            db.session.add(u1)
            db.session.add(u2)
            db.session.add(u3)
            db.session.add(u4)
            db.session.add(u5)
            db.session.add(u6)
            db.session.add(u7)

            db.session.commit()

            # Creazione fascicoli

            f1  = Files(rg16="101", rg20="268", rg21="269", anno="2022")
            f2  = Files(rg16="102", rg20="864", rg21="",    anno="2022")
            f3  = Files(rg16="116", rg20="874", rg21="295", anno="2022")
            f4  = Files(rg16="165", rg20="478", rg21="478", anno="2022")
            f5  = Files(rg16="197", rg20="125", rg21="565", anno="2022")
            f6  = Files(rg16="263", rg20="",    rg21="",    anno="2022")
            f7  = Files(rg16="572", rg20="",    rg21="",    anno="2022")
            f8  = Files(rg16="467", rg20="",    rg21="",    anno="2022")
            f9  = Files(rg16="276", rg20="",    rg21="",    anno="2022")
            f10 = Files(rg16="763", rg20="",    rg21="852", anno="2022")
            f11 = Files(rg16="472", rg20="",    rg21="246", anno="2022")
            f12 = Files(rg16="863", rg20="",    rg21="148", anno="2022")

            db.session.add(f1)
            db.session.add(f2)
            db.session.add(f3)
            db.session.add(f4)
            db.session.add(f5)
            db.session.add(f6)
            db.session.add(f7)
            db.session.add(f8)
            db.session.add(f9)
            db.session.add(f10)
            db.session.add(f11)
            db.session.add(f12)

            db.session.commit()

            f1.generate_qr()

            # Creazione history

            h11 = History(user_id=u1.id, file_id=f1.id, created=datetime(2022, 11, 4, 10, 30))
            h12 = History(user_id=u2.id, file_id=f1.id, created=datetime(2022, 11, 4, 11, 18))
            h13 = History(user_id=u1.id, file_id=f1.id, created=datetime(2022, 11, 4, 17, 10))

            h21  = History(user_id=u1.id, file_id=f2.id,  created=datetime(2022, 11, 4,  13, 35))
            h31  = History(user_id=u5.id, file_id=f3.id,  created=datetime(2022, 11, 1,  16, 29))
            h41  = History(user_id=u6.id, file_id=f4.id,  created=datetime(2022, 10, 29, 9,  40))
            h51  = History(user_id=u7.id, file_id=f5.id,  created=datetime(2022, 11, 2,  15, 1))
            h61  = History(user_id=u1.id, file_id=f6.id,  created=datetime(2022, 11, 2,  13, 14))
            h71  = History(user_id=u5.id, file_id=f7.id,  created=datetime(2022, 10, 26, 14, 53))
            h81  = History(user_id=u6.id, file_id=f8.id,  created=datetime(2022, 10, 27, 8,  34))
            h91  = History(user_id=u7.id, file_id=f9.id,  created=datetime(2022, 11, 3,  15, 54))
            h101 = History(user_id=u1.id, file_id=f10.id, created=datetime(2022, 11, 7,  13, 18))
            h111 = History(user_id=u7.id, file_id=f11.id, created=datetime(2022, 11, 4,  7,  45))
            h121 = History(user_id=u5.id, file_id=f12.id, created=datetime(2022, 10, 28, 10, 15))

            h22  = History(user_id=u5.id, file_id=f2.id,  created=datetime(2022, 11, 4,  15, 55))
            h32  = History(user_id=u6.id, file_id=f3.id,  created=datetime(2022, 11, 2,  10, 57))
            h42  = History(user_id=u7.id, file_id=f4.id,  created=datetime(2022, 11, 2,  7,  55))
            h52  = History(user_id=u1.id, file_id=f5.id,  created=datetime(2022, 11, 3,  10, 16))
            h62  = History(user_id=u5.id, file_id=f6.id,  created=datetime(2022, 11, 2,  18, 14))
            h72  = History(user_id=u6.id, file_id=f7.id,  created=datetime(2022, 10, 29, 10, 24))
            h82  = History(user_id=u7.id, file_id=f8.id,  created=datetime(2022, 10, 27, 14, 56))
            h92  = History(user_id=u1.id, file_id=f9.id,  created=datetime(2022, 11, 4,  15, 34))
            h102 = History(user_id=u5.id, file_id=f10.id, created=datetime(2022, 11, 7,  14, 29))
            h112 = History(user_id=u6.id, file_id=f11.id, created=datetime(2022, 11, 4,  17, 15))
            h122 = History(user_id=u7.id, file_id=f12.id, created=datetime(2022, 10, 28, 16, 14))



            db.session.add(h11)
            db.session.add(h12)
            db.session.add(h13)

            db.session.add(h21)
            db.session.add(h31)
            db.session.add(h41)
            db.session.add(h51)
            db.session.add(h61)
            db.session.add(h71)
            db.session.add(h81)
            db.session.add(h91)
            db.session.add(h101)
            db.session.add(h111)
            db.session.add(h121)

            db.session.add(h22)
            db.session.add(h32)
            db.session.add(h42)
            db.session.add(h52)
            db.session.add(h62)
            db.session.add(h72)
            db.session.add(h82)
            db.session.add(h92)
            db.session.add(h102)
            db.session.add(h112)
            db.session.add(h122)

            db.session.commit()
