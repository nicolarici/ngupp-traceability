from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from app.models import User, Files
from app.extension import db
import config
import datetime

def numero_fascicoli_ufficio(ufficio):
    return Files.query.filter_by(ufficio=ufficio).count()

def media_tempo_per_ufficio(ufficio):
    files=Files.query.filter_by(ufficio=ufficio).all()
    media=datetime.timedelta()
    for file in files:
        media=media+file.created
    return media/len(files)

class statistic():
    def __init__(self, ufficio):
        self.ufficio=ufficio
        self.numero_fascicoli=numero_fascicoli_ufficio(ufficio)
        self.media_tempo=media_tempo_per_ufficio(ufficio)

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@bp.route('/view', methods=('GET', 'POST'))
@login_required
def view():
    
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()
    uffici=[]
    for user in users:
        uffici.append(user.ufficio)
    
    for ufficio in uffici:
        
        print(statistic(ufficio).ufficio)
        print(statistic(ufficio).numero_fascicoli)
        print(statistic(ufficio).media_tempo)
    
    return render_template('statistics/view.html', title=current_app.config["LABELS"]["statistics"])
