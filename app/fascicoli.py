import code
import datetime
import qrcode
from pathlib import Path
from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_login import login_required,current_user
from app.models import Files
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from app.models import User
from app.extension import db

def generate_qr_code(file_name):
    img = qrcode.make(current_app.config["BASE_URL"] + "fascicoli/" + file_name + "/add")
    downloads_path = str(Path.home() / "Downloads")
    img.save(downloads_path + f"/{file_name}.png")


bp = Blueprint('fascicoli', __name__, url_prefix='/fascicoli')

@bp.route('/generation', methods=('GET', 'POST'))
@login_required
def generation():

    class GenerationForm(FlaskForm):
        codice = StringField(current_app.config["LABELS"]["codice"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["genera"])
    
    form = GenerationForm()
    if form.validate_on_submit():
        
        generate_qr_code(form.codice.data)
        
        file = Files(code=form.codice.data, user_id=current_user.id, user_name=current_user.nome+" "+current_user.cognome, user_office=current_user.ufficio)
        
        db.session.add(file)
        db.session.commit()

        files = Files.query.filter_by(code=form.codice.data).first()

        return redirect(url_for('fascicoli.file_details', code=form.codice.data))

    return render_template('qr_generation/generate_code.html', title=current_app.config["LABELS"]["generation_title"], form=form)

@bp.route('/<code>', methods=('GET', 'POST'))
@login_required
def file_details(code):
    
    files = Files.query.filter_by(code=code).order_by(Files.created).all()
    
    
    return render_template('qr_generation/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], files=files)

@bp.route('/<code>/add', methods=('GET', 'POST'))
@login_required
def file_add(code):
    
    file = Files(code=code, user_id=current_user.id, user_name=current_user.nome+" "+current_user.cognome, user_office=current_user.ufficio)
        
    db.session.add(file)
    db.session.commit()
    
    files = Files.query.filter_by(code=code).order_by(Files.created).all()
    
    
    return render_template('qr_generation/file_details.html', title=current_app.config["LABELS"]["storico_fascicolo"], files=files)