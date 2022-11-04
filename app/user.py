from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request, Markup
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.validators import DataRequired
from app.models import User
from app.widgets import CustomStringField
from app.extension import db


bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/<id>', methods=('GET', 'POST'))
@login_required
def user(id):

    user = User.query.filter_by(id=id).first_or_404()

    class ModifyUserForm(FlaskForm):
                                      
        nome = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["nome"] + "</strong>"), 
                                 default=user.nome,
                                 validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        cognome = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["cognome"] + "</strong>"), 
                                    default=user.cognome,
                                    validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        nome_ufficio = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["nome_ufficio_opz"] + "</strong>"), 
                                         default=user.nome_ufficio)
        
        ufficio = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["ufficio"] + "</strong>"), 
                                    default=user.ufficio, 
                                    validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["modify"])

    form = ModifyUserForm()
    if form.validate_on_submit():

        if user.nome == form.nome.data and user.cognome == form.cognome.data and user.nome_ufficio == form.nome_ufficio.data and user.ufficio == form.ufficio.data:
            flash(current_app.config["LABELS"]["no_change"], "info")
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
    return render_template('user/visualizza_utenti.html')


@bp.route('/promote/<user_id>', methods=('GET', 'POST'))
@login_required
def promote(user_id):
    
    user = User.query.filter_by(id=user_id).first()
    user.superuser = True
    db.session.commit()

    return redirect(url_for('user.see_users'))


@bp.route('/demote/<user_id>', methods=('GET', 'POST'))
@login_required
def demote(user_id):

    user = User.query.filter_by(id=user_id).first()
    user.superuser = False
    db.session.commit()
    
    return redirect(url_for('user.see_users'))


@bp.route('/api/data')
@login_required
def data():
    query = User.query.filter(User.email != current_app.config["ADMIN_MAIL"])

    # search filter
    search = request.args.get('search[value]')
    if search:
        query = query.filter(db.or_(
            User.nome.like(f'%{search}%'),
            User.cognome.like(f'%{search}%'),
            User.nome_ufficio.like(f'%{search}%'),
            User.ufficio.like(f'%{search}%'),
            User.email.like(f'%{search}%')
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
        col = getattr(User, col_code)
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

    
    def render_file(user):
        if user.superuser:
            bottone = '<a  href="demote/' + str(user.id) + '" class="btn btn-danger btn-sm" role="button" aria-pressed="true">Revoca Privilegi</a>'
        else:
            bottone = '<a  href="promote/' + str(user.id) + '" class="btn btn-success btn-sm" role="button" aria-pressed="true">Assegna Privilegi</a>'
            
        return {
            'nome_utente': user.nome + ' ' + user.cognome,
            'email_utente': user.email,
            'ufficio': user.ufficio,
            'nome_ufficio': user.nome_ufficio,
            'privilegi': bottone

        }

    return {
        'data': [render_file(file) for file in query],
        'recordsFiltered': total_filtered,
        'recordsTotal': User.query.count(),
        'draw': request.args.get('draw', type=int),
    }