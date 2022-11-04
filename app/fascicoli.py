import os
import qrcode
from flask import Blueprint, render_template, url_for, current_app, redirect, flash, send_from_directory, request, Markup
from flask_login import login_required, current_user
from app.models import Files, History
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField
from wtforms.widgets import NumberInput
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import User
from app.extension import db
from app.widgets import CustomIntegerField
from datetime import datetime


def generate_qr(file_id):

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(current_app.config["BASE_URL"] + f"fascicoli/{file_id}/add")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"app/static/img/QR_{file_id}.png")

        return
    

bp = Blueprint('fascicoli', __name__, url_prefix='/fascicoli')


@bp.route('/<file_id>/download', methods=['GET', 'POST'])
def download(file_id):
    uploads = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, f"QR_{file_id}.png", as_attachment=True)


@bp.route('/generation', methods=('GET', 'POST'))
@login_required
def generation():

    class GenerationForm(FlaskForm):
        rg21 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg21"] + "</strong>"), 
                            widget=NumberInput(min=1, step=1), 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        rg20 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg20"] + "</strong>"), 
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional(), NumberRange(min=0)])
        rg16 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg16"] + "</strong>"), 
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional()])
        anno = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["anno"] + "</strong>"), 
                            widget=NumberInput(min=1, step=1), 
                            default=datetime.now().year,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["crea"])
    
    form = GenerationForm()
    if form.validate_on_submit():

        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"], "danger")
            return redirect(url_for('fascicoli.generation'))
        
        file = Files(rg21=form.rg21.data,
                     rg20=form.rg20.data,
                     rg16=form.rg16.data,
                     anno=form.anno.data)
                     
        db.session.add(file)
        db.session.commit()

        file = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).first()
        generate_qr(file.id)

        return redirect(url_for('fascicoli.file_add', file_id=file.id))

    return render_template('fascicoli/base_information_form.html', title=current_app.config["LABELS"]["generation_title"],
                            crea=True, modifica=False, form=form, btn_map={"submit": "primary"})


@bp.route('/api/data/<file_id>')
@login_required
def data(file_id):
    query = History.query.filter_by(file_id=file_id).join(User, User.id == History.user_id).add_columns(User.nome, User.cognome, User.nome_ufficio, User.ufficio, History.user_id, History.created, History.id, History.duplicate_from).order_by(History.created.desc())
    
    # search filter
    search = request.args.get('search[value]')
    if search:
        query = query.filter(db.or_(
            User.nome.like(f'%{search}%'),
            User.cognome.like(f'%{search}%'),
            User.nome_ufficio.like(f'%{search}%'),
            User.ufficio.like(f'%{search}%'),
            History.created.like(f'%{search}%')
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


    def render_file(hist):

        if hist.duplicate_from == -1 and hist.user_id is current_user.id:
            btn = '<div class="d-grid gap-2"><a class="btn btn-sm btn-danger" href="' + str(hist.id) + '/hist_delete" type="button"">' + current_app.config["LABELS"]["elimina"] + '</a></div>'
        elif hist.duplicate_from > -1:
            btn = '<div class="d-grid gap-2"><a class="btn btn-sm btn-success" href="/fascicoli/' + str(hist.duplicate_from) + '" type="button">' + current_app.config["LABELS"]["vis_dup"] + '</a></div>'
        else: 
            btn = ''

        return {
            'user_name': hist.nome + ' ' + hist.cognome,
            'office_name': hist.nome_ufficio,
            'office_number': hist.ufficio,
            'created': hist.created.strftime(' %H:%M - %d/%m/%Y '),
            'btn': btn
        }

    # response
    return {
        'data': [render_file(file) for file in query],
        'recordsFiltered': total_filtered,
        'recordsTotal': Files.query.count(),
        'draw': request.args.get('draw', type=int),
    }


@bp.route('/<file_id>', methods=('GET', 'POST'))
@login_required
def file_details(file_id):    
    return render_template('fascicoli/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], file=Files.query.get(file_id))


@bp.route('/<file_id>/add', methods=('GET', 'POST'))
@login_required
def file_add(file_id):

    last = History.query.filter_by(file_id=file_id).order_by(History.created.desc()).first()

    if last is None or (last is not None and last.user_id != current_user.id):
        new_hist = History(file_id=file_id, created=datetime.now(), user_id=current_user.id)
        db.session.add(new_hist)
        db.session.commit()
    
    return redirect(url_for('fascicoli.file_details', file_id=file_id))


@bp.route('/<file_id>/delete', methods=('GET', 'POST'))
@login_required
def file_delete(file_id):
    
    hist = History.query.filter_by(file_id=file_id).all()
    for h in hist:
        db.session.delete(h)

    file = Files.query.filter_by(id=file_id).first()
    db.session.delete(file)
    db.session.commit()

    os.remove(f"app/static/img/QR_{file_id}.png")
    
    return redirect(url_for('index'))


@bp.route('/<hist_id>/hist_delete', methods=('GET', 'POST'))
@login_required
def record_delete(hist_id):
    
    hist = History.query.filter_by(id=hist_id).first()

    all_hist = History.query.filter_by(file_id=hist.file_id).all()

    if len(all_hist) > 1:
        db.session.delete(hist)
        db.session.commit()
    else:
        flash(current_app.config["LABELS"]["last_hist_delete_error"], "danger")

    return redirect(url_for('fascicoli.file_details', file_id=hist.file_id))


@bp.route('/<file_id>/duplica', methods=('GET', 'POST'))
@login_required
def file_duplicate(file_id):

    file = Files.query.filter_by(id=file_id).first()

    class DuplicateForm(FlaskForm):
        rg21 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg21"] + "</strong>"), 
                            default=file.rg21,
                            widget=NumberInput(min=1, step=1), 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        rg20 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg20"] + "</strong>"), 
                            default=file.rg20,
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional(), NumberRange(min=0)])
        rg16 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg16"] + "</strong>"), 
                            default=file.rg16,
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional()])
        anno = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["anno"] + "</strong>"), 
                            default=file.anno,
                            widget=NumberInput(min=1, step=1), 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["duplica"])
    
    form = DuplicateForm()
    if form.validate_on_submit():
      
        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"], "danger")
            return redirect(url_for('fascicoli.file_duplicate', file_id=file_id))

        dup_file = Files(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data, parent=file_id)
        db.session.add(dup_file)
        db.session.commit()

        file = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).first()
        generate_qr(dup_file.id)

        # Copy file history

        hist = History.query.filter_by(file_id=file_id).all()
        for h in hist:
            new_hist = History(file_id=file.id, created=h.created, user_id=h.user_id)
            db.session.add(new_hist)
        db.session.commit()

        # Add new history

        new_hist = History(file_id=file_id, created=datetime.now(), user_id=current_user.id, duplicate_from=file.id)
        db.session.add(new_hist)

        new_hist_dup = History(file_id=file.id, created=datetime.now(), user_id=current_user.id, duplicate_from=file_id)
        db.session.add(new_hist_dup)

        db.session.commit()

        return redirect(url_for('fascicoli.file_add', file_id=file.id))
        

    return render_template('fascicoli/base_information_form.html', title=current_app.config["LABELS"]["generation_title"], 
                            crea=False, modifica=False, form=form, btn_map={"submit": "primary"})


@bp.route('/<file_id>/modifica', methods=('GET', 'POST'))
@login_required
def file_modify(file_id):

    file = Files.query.filter_by(id=file_id).first()

    class ModifyForm(FlaskForm):
        rg21 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg21"] + "</strong>"), 
                            default=file.rg21,
                            widget=NumberInput(min=1, step=1), 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
                            
        rg20 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg20"] + "</strong>"), 
                            default=file.rg20,
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional(), NumberRange(min=0)])

        rg16 = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["rg16"] + "</strong>"), 
                            default=file.rg16,
                            widget=NumberInput(min=1, step=1), 
                            validators=[Optional()])

        anno = CustomIntegerField(Markup("<strong>" + current_app.config["LABELS"]["anno"] + "</strong>"), 
                            default=file.anno,
                            widget=NumberInput(min=1, step=1), 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["modifica"])
    
    form = ModifyForm()
    if form.validate_on_submit():

        if file.rg21 == form.rg21.data and file.rg20 == form.rg20.data and file.rg16 == form.rg16.data and file.anno == form.anno.data:
            flash(current_app.config["LABELS"]["no_change"], "info")
            return redirect(url_for('fascicoli.file_details', file_id=file_id))

        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"], "danger")
            return redirect(url_for('fascicoli.file_modify', file_id=file_id))

        file.rg21 = form.rg21.data
        file.rg20 = form.rg20.data
        file.rg16 = form.rg16.data
        file.anno = form.anno.data

        db.session.add(file)
        db.session.commit()

        return redirect(url_for('fascicoli.file_details', file_id=file.id))
        

    return render_template('fascicoli/base_information_form.html', title=current_app.config["LABELS"]["generation_title"], 
                            crea=False, modifica=True, form=form, btn_map={"submit": "primary"})