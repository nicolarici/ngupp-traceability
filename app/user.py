from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from app.models import User
from app.extension import db

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/<id>', methods=('GET', 'POST'))
@login_required
def user(id):

    user = User.query.filter_by(id=id).first_or_404()

    class ModifyUserForm(FlaskForm):
                                      
        nome = StringField(current_app.config["LABELS"]["nome"], 
                        default=user.nome,
                        validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        cognome = StringField(current_app.config["LABELS"]["cognome"], 
                        default=user.cognome,
                        validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        nome_ufficio = StringField(current_app.config["LABELS"]["nome_ufficio_opz"], 
                        default=user.nome_ufficio)
        
        ufficio = StringField(current_app.config["LABELS"]["ufficio"], 
                        default=user.ufficio, 
                        validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["modify"])

    form = ModifyUserForm()
    if form.validate_on_submit():

        if user.nome == form.nome.data and user.cognome == form.cognome.data and user.nome_ufficio == form.nome_ufficio.data and user.ufficio == form.ufficio.data:
            flash(current_app.config["LABELS"]["no_change"])
            return redirect(url_for('index'))

        user.nome = form.nome.data
        user.cognome = form.cognome.data
        user.ufficio = form.ufficio.data
        user.nome_ufficio = form.nome_ufficio.data

        db.session.commit()

        flash(current_app.config["LABELS"]["user_modified"], "success")

        return redirect(url_for('index', id=user.id))

    return render_template('user/profilo.html', form=form, btn_map={"submit": "primary"})


@bp.route('/utenti', methods=('GET', 'POST'))
@login_required
def see_users():
    users = User.query.filter(User.email != current_app.config["ADMIN_MAIL"]).all()
    
    return render_template('user/visualizza_utenti.html', users=users)


@bp.route('/promote/<user_id>', methods=('GET', 'POST'))
@login_required
def promote(user_id):
    
    user = User.query.filter_by(id=user_id).first()
    user.superuser = True
    
    db.session.add(user)
    db.session.commit()
    
    users = User.query.filter(User.email != current_app.config["ADMIN_MAIL"]).all()

    return render_template('user/visualizza_utenti.html', title=current_app.config["LABELS"]["lista_utenti"], users=users)


@bp.route('/demote/<user_id>', methods=('GET', 'POST'))
@login_required
def demote(user_id):
    user = User.query.filter_by(id=user_id).first()
    user.superuser = False
    
    db.session.commit()
    
    users=User.query.filter(User.email!=current_app.config["ADMIN_MAIL"]).all()

    return render_template('user/visualizza_utenti.html', title=current_app.config["LABELS"]["lista_utenti"], users=users)
