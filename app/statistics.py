from flask import Blueprint, render_template, current_app
from flask_login import login_required
from app.models import User, Files, History
from app.extension import db


class Statistic():
    def __init__(self, ufficio, nome_ufficio):
        self.ufficio = ufficio
        self.nome_ufficio = nome_ufficio
        self.numero_fascicoli = self.numero_fascicoli_ufficio(ufficio)
        self.media_tempo = self.media_tempo_per_ufficio(ufficio)

    @staticmethod
    def numero_fascicoli_ufficio(ufficio):
        return db.session.query(User, History, Files).filter(User.id == History.user_id).filter(History.file_id == Files.id).filter(User.ufficio==ufficio).count()
    
def media_tempo_per_ufficio(ufficio):
    files=db.session.query(User, History, Files).filter(User.id == History.user_id).filter(History.file_id == Files.id).filter(User.ufficio==ufficio).order_by(History.created.asc()).all()
    tempo_totale=0
    for i in range(len(files)-1):
        tempo_totale=tempo_totale+(files[i+1][1].created-files[i][1].created).total_seconds()
    if tempo_totale == 0 or len(files) == 0:
        return "0"
        
    return GetTime(round(tempo_totale/len(files)))

    
    def getTime(time):
        day = time // (24 * 3600)
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        
        if day == 0 and hour == 0 and minutes == 0:
            return "%d m" %  1
        elif day == 0 and hour == 0:
            return "%d m" % (minutes)
        elif day == 0:
            return "%d o %d m" % (hour, minutes)
        else:
            return "%d g, %d o, %d m" % (day, hour, minutes)


bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@bp.route('/view', methods=('GET', 'POST'))
@login_required
def view():
    return render_template('statistics/statistics.html', title=current_app.config["LABELS"]["statistics"])


@bp.route('/api/data')
@login_required
def data():
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()
    uffici=[]
    for user in users:
        uffici.append([user.ufficio, user.nome_ufficio])
    statistics= []
    
    for ufficio in uffici:
        if numero_fascicoli_ufficio(ufficio[0]) != 0:
            statistics.append(Statistic(ufficio[0], ufficio[1]))
                    
    def render_file(stat):
        return {
            'ufficio': stat.ufficio,
            'nome_ufficio': stat.nome_ufficio,
            'numero_fascicoli': stat.numero_fascicoli,
            'media_tempo': stat.media_tempo
        }
    return {'data': [render_file(stat) for stat in statistics]}

    
    