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
        
        file = Files(rg21=form.rg21.data,
                     rg20=form.rg20.data,
                     rg16=form.rg16.data,
                     anno=form.anno.data)
                     
        db.session.add(file)
        db.session.commit()

        # Create QR code

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        file = Files.query.order_by(Files.id.desc()).first()

        qr.add_data(current_app.config["BASE_URL"] + f"fascicoli/{file.id}/add")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"app/static/img/{file.id}.png")

        return redirect(url_for('fascicoli.file_add', file_id=file.id))

    return render_template('fascicoli/generate_code.html', title=current_app.config["LABELS"]["generation_title"], form=form)


@bp.route('/<file_id>', methods=('GET', 'POST'))
@login_required
def file_details(file_id):
    
    history = History.query.filter_by(file_id=file_id).join(User, User.id == History.user_id).add_columns(User.nome, User.cognome, User.nome_ufficio, User.ufficio, History.created, History.id).order_by(History.created.desc()).all()
    
    return render_template('fascicoli/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], files=history, file_id=file_id)


@bp.route('/<file_id>/add', methods=('GET', 'POST'))
@login_required
def file_add(file_id):
    
    file = History(file_id=file_id, created=datetime.now(), user_id=current_user.id)
    db.session.add(file)
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
    
    return redirect(url_for('index'))


@bp.route('/<hist_id>/delete', methods=('GET', 'POST'))
@login_required
def record_delete(hist_id):
    
    file = History.query.filter_by(hist_id=hist_id).first()

    db.session.delete(file)
    db.session.commit()

    return redirect(url_for('fascicoli.file_details', file_id=file.id))