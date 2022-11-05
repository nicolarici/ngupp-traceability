from flask import Blueprint, render_template, current_app
from flask_login import login_required
from app.models import User, Files, History
from app.extension import db


class Statistic():
    def __init__(self, user):
        
        self.user = user
        self.numero_fascicoli = db.session.query(History).filter(user.id == History.user_id).count()
        
        if self.numero_fascicoli > 0:
            self.media_tempo = self.media_tempo_per_ufficio(user, self.numero_fascicoli)
        else:
            self.media_tempo = 0
    
    def media_tempo_per_ufficio(self, user, num_fas):
                    
        files_hist = db.session.query(History).order_by(History.file_id, History.created).all()
        
        tempo_totale = 0
        for i in range(len(files_hist)-1):
            if files_hist[i].file_id == files_hist[i+1].file_id:
                if files_hist[i].user_id == user.id:
                    tempo_totale=tempo_totale+(files_hist[i+1].created-files_hist[i].created).total_seconds()

        return round(tempo_totale/num_fas)
    
    """ def getTime(self, time):
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
            return "%d g, %d o, %d m" % (day, hour, minutes) """


bp = Blueprint('statistics', __name__, url_prefix='/statistics')


@bp.route('/view', methods=('GET', 'POST'))
@login_required
def view():
    return render_template('statistics/statistics.html')


@bp.route('/api/data')
@login_required
def data():
    users = User.query.filter(User.email != current_app.config["ADMIN_MAIL"]).all()
    
    statistics = []
    for user in users:
        statistic = Statistic(user)
        
        if statistic.numero_fascicoli > 0 and statistic.media_tempo > 0:
            statistics.append(statistic)
                    
    def render_file(stat):
        return {
            'nome_utente': stat.user.nome+" "+stat.user.cognome,
            'numero_ufficio': stat.user.ufficio,
            'nome_ufficio': stat.user.nome_ufficio,
            'numero_fascicoli': stat.numero_fascicoli,
            'media_tempo': stat.media_tempo
        }
    
    return {'data': [render_file(stat) for stat in statistics]}
