from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Regexp
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.extension import db


bp = Blueprint('auth', __name__, url_prefix='/auth')

# Login view

@bp.route('/register', methods=('GET', 'POST'))
def register():

    class RegistrationForm(FlaskForm):
        email = StringField(current_app.config["LABELS"]["email"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                        Email(message=current_app.config["LABELS"]["email_error"])])
                                        
        password = PasswordField(current_app.config["LABELS"]["password"], 
                                validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                            EqualTo('confirm', message=current_app.config["LABELS"]["password_match_error"]),
                                            Regexp("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", message=current_app.config["LABELS"]["password_error"])])

        confirm  = PasswordField(current_app.config["LABELS"]["confirm_password"])

        ufficio = StringField(current_app.config["LABELS"]["ufficio"], 
                        validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["registration"])


        def validate_email(self, email):

            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError(current_app.config["LABELS"]["email_alredy_used"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit(): #and form.email.data[-13:] == "@giustizia.it":

        nome, cognome = form.email.data.split("@")[0].split(".")

        user = User(nome=nome, cognome=cognome, email=form.email.data, ufficio=form.ufficio.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()


        # Invia e-mail di conferma account.

        import smtplib, ssl

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(current_app.config["MAIL_SERVER"], context=context) as server:
            server.sendmail(current_app.config["MAIL_SENDER"], form.email.data, "Registrazione completata")

        return redirect(url_for('auth.login'))


    return render_template('auth/register.html', 
                           title=current_app.config["LABELS"]["registration_title"], 
                           form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():

    class LoginForm(FlaskForm):
        email = StringField(current_app.config["LABELS"]["email"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                        Email(message=current_app.config["LABELS"]["email_error"])])
                                        
        password = PasswordField(current_app.config["LABELS"]["password"], 
                                validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        remember_me = BooleanField(current_app.config["LABELS"]["remember_me"])

        submit = SubmitField(current_app.config["LABELS"]["login"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash(current_app.config["LABELS"]["login_error"])
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('auth/login.html', title=current_app.config["LABELS"]["login_title"], form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))