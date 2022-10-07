from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from app.models import User
from app.extension import db

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/user/<id>', methods=('GET', 'POST'))
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

        ufficio = StringField(current_app.config["LABELS"]["ufficio"], 
                        default=user.ufficio, 
                        validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["modify"])

    form = ModifyUserForm()

    if form.validate_on_submit():

        user.nome = form.nome.data
        user.cognome = form.cognome.data
        user.ufficio = form.ufficio.data

        db.session.commit()

        flash(current_app.config["LABELS"]["user_modified"], "success")

        return redirect(url_for('user.user', id=user.id))

    return render_template('user/user.html', form=form)