import code
import datetime
import qrcode
from pathlib import Path
from flask import Blueprint, render_template, url_for, current_app, redirect, flash, send_from_directory
from flask_login import login_required,current_user
from app.models import Files
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from app.models import User
from app.extension import db
import os
from datetime import datetime

def generate_and_download_qr_code(code):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(current_app.config["BASE_URL"] + f"fascicoli/{code}/add")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"app/static/img/{code}.png")

    return


bp = Blueprint('fascicoli', __name__, url_prefix='/fascicoli')


@bp.route('/download/<code>', methods=['GET', 'POST'])
def download(code):
    uploads = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, f"{code}.png", as_attachment=True)


@bp.route('/generation', methods=('GET', 'POST'))
@login_required
def generation():

    class GenerationForm(FlaskForm):
        codice = IntegerField(current_app.config["LABELS"]["codice"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])
        anno= IntegerField(current_app.config["LABELS"]["codice_anno"], 
                            default=datetime.datetime.now().year,
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["genera"])
    
    form = GenerationForm()
    if form.validate_on_submit():
        
        if db.session.query(Files.code).filter_by(code=str(form.codice.data)+"-"+str(form.anno.data)).scalar() is not None:
            flash(current_app.config["LABELS"]["codice_esistente"])
            return redirect(url_for('fascicoli.generation'))
        
        generate_and_download_qr_code(str(form.codice.data)+"-"+str(form.anno.data))
        
        file = Files(code=str(form.codice.data)+"-"+str(form.anno.data), created=datetime.now(), user_id=current_user.id)
        
        db.session.add(file)
        db.session.commit()

        return redirect(url_for('fascicoli.file_details', code=str(form.codice.data)+"-"+str(form.anno.data)))

    return render_template('qr_generation/generate_code.html', title=current_app.config["LABELS"]["generation_title"], form=form)


@bp.route('/<code>', methods=('GET', 'POST'))
@login_required
def file_details(code):
    
    files = Files.query.filter_by(code=code).join(User, User.id == Files.user_id).add_columns(User.nome, User.cognome, User.ufficio, Files.code, Files.created).order_by(Files.created.desc()).all()
    
    return render_template('qr_generation/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], files=files, code=code)


@bp.route('/<code>/add', methods=('GET', 'POST'))
@login_required
def file_add(code):
    
    file = Files(code=code, created=datetime.now(), user_id=current_user.id)
        
    db.session.add(file)
    db.session.commit()
    
    
    return redirect(url_for('fascicoli.file_details', code=code))


@bp.route('/<code>/delete', methods=('GET', 'POST'))
@login_required
def file_delete(code):
    
    files = Files.query.filter_by(code=code).all()
    for file in files:
        db.session.delete(file)
    db.session.commit()
    
    return redirect(url_for('index'))