from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from app.models import User
from app.extension import db
import config



bp = Blueprint('superuser', __name__, url_prefix='/su')

@bp.route('/utenti', methods=('GET', 'POST'))
@login_required
def see_users():
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()
    
    return render_template('superuser/visualizza_utenti.html', title=current_app.config["LABELS"]["lista_utenti"], users=users)

@bp.route('/promote/<user_id>', methods=('GET', 'POST'))
@login_required
def promote(user_id):
    
    user=User.query.filter_by(id=user_id).first()
    user.superuser=True
    
    db.session.add(user)
    db.session.commit()
    
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()

    return render_template('superuser/visualizza_utenti.html', title=current_app.config["LABELS"]["lista_utenti"], users=users)

@bp.route('/demote/<user_id>', methods=('GET', 'POST'))
@login_required
def demote(user_id):
    user=User.query.filter_by(id=user_id).first()
    user.superuser=False
    
    db.session.commit()
    
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()

    return render_template('superuser/visualizza_utenti.html', title=current_app.config["LABELS"]["lista_utenti"], users=users)
