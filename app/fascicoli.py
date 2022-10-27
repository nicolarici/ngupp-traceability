import os
import qrcode
from flask import Blueprint, render_template, url_for, current_app, redirect, flash, send_from_directory
from flask_login import login_required,current_user
from app.models import Files, History
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional
from app.models import User
from app.extension import db
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
        img.save(f"app/static/img/{file_id}.png")

        return
    

bp = Blueprint('fascicoli', __name__, url_prefix='/fascicoli')


@bp.route('/<file_id>/download', methods=['GET', 'POST'])
def download(file_id):
    uploads = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, f"{file_id}.png", as_attachment=True)


@bp.route('/generation', methods=('GET', 'POST'))
@login_required
def generation():

    class GenerationForm(FlaskForm):
        rg21 = IntegerField(current_app.config["LABELS"]["rg21"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        rg20 = IntegerField(current_app.config["LABELS"]["rg20"], validators=[Optional()])
        rg16 = IntegerField(current_app.config["LABELS"]["rg16"], validators=[Optional()])
        anno = IntegerField(current_app.config["LABELS"]["codice_anno"], 
                            default=datetime.now().year,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["genera"])
    
    form = GenerationForm()
    if form.validate_on_submit():

        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"])
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

    return render_template('fascicoli/generate_code.html', title=current_app.config["LABELS"]["generation_title"], form=form)


@bp.route('/<file_id>', methods=('GET', 'POST'))
@login_required
def file_details(file_id):
    
    history = History.query.filter_by(file_id=file_id).join(User, User.id == History.user_id).add_columns(User.nome, User.cognome, User.nome_ufficio, User.ufficio, History.user_id, History.created, History.id).order_by(History.created.desc()).all()
    
    return render_template('fascicoli/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], hist=history, file=Files.query.get(file_id))


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

    os.remove(f"app/static/img/{file_id}.png")
    
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
        flash("Non puoi eliminare l'unico record. Elimina l'intero fascicolo.")

    return redirect(url_for('fascicoli.file_details', file_id=hist.file_id))


@bp.route('/<file_id>/duplica', methods=('GET', 'POST'))
@login_required
def file_duplicate(file_id):

    file = Files.query.filter_by(id=file_id).first()

    class DuplicateForm(FlaskForm):
        rg21 = IntegerField(current_app.config["LABELS"]["rg21"], 
                            default=file.rg21,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        rg20 = IntegerField(current_app.config["LABELS"]["rg20"], validators=[Optional()], default=file.rg20)
        rg16 = IntegerField(current_app.config["LABELS"]["rg16"], validators=[Optional()], default=file.rg16)
        anno = IntegerField(current_app.config["LABELS"]["codice_anno"], 
                            default=file.anno,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["duplica"])
    
    form = DuplicateForm()
    if form.validate_on_submit():
      
        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"])
            return redirect(url_for('fascicoli.file_duplicate', file_id=file_id))

        dup_file = Files(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data)
        db.session.add(dup_file)
        db.session.commit()

        file = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).first()
        generate_qr(dup_file.id)

        return redirect(url_for('fascicoli.file_add', file_id=file.id))
        

    return render_template('fascicoli/modifica.html', title=current_app.config["LABELS"]["generation_title"], duplica=True, form=form)


@bp.route('/<file_id>/modifica', methods=('GET', 'POST'))
@login_required
def file_modify(file_id):

    file = Files.query.filter_by(id=file_id).first()

    class ModifyForm(FlaskForm):
        rg21 = IntegerField(current_app.config["LABELS"]["rg21"], 
                            default=file.rg21,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        rg20 = IntegerField(current_app.config["LABELS"]["rg20"], validators=[Optional()], default=file.rg20)
        rg16 = IntegerField(current_app.config["LABELS"]["rg16"], validators=[Optional()], default=file.rg16)
        anno = IntegerField(current_app.config["LABELS"]["codice_anno"], 
                            default=file.anno,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["modifica"])
    
    form = ModifyForm()
    if form.validate_on_submit():

        if file.rg21 == form.rg21.data and file.rg20 == form.rg20.data and file.rg16 == form.rg16.data and file.anno == form.anno.data:
            print("IN")
            flash(current_app.config["LABELS"]["no_change"])
            return redirect(url_for('fascicoli.file_details', file_id=file_id))

        print("OUT")
        files = Files.query.filter_by(rg21=form.rg21.data, rg20=form.rg20.data, rg16=form.rg16.data, anno=form.anno.data).all()

        if len(files) > 0:
            flash(current_app.config["LABELS"]["duplicate_error"])
            return redirect(url_for('fascicoli.file_modify', file_id=file_id))

        file.rg21 = form.rg21.data
        file.rg20 = form.rg20.data
        file.rg16 = form.rg16.data
        file.anno = form.anno.data

        db.session.add(file)
        db.session.commit()

        return redirect(url_for('fascicoli.file_details', file_id=file.id))
        

    return render_template('fascicoli/modifica.html', title=current_app.config["LABELS"]["generation_title"], duplica=False, form=form)