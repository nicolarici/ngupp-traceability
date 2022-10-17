from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Regexp
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.extension import db, mail
from flask_mail import Message


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    with current_app.app_context():
        mail.send(msg)


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

    if form.validate_on_submit() and form.email.data[-13:] == "@giustizia.it":

        nome, cognome = form.email.data.split("@")[0].split(".")

        user = User(nome=nome.capitalize(), cognome=cognome.capitalize(), email=form.email.data, ufficio=form.ufficio.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()


        # Invia e-mail di conferma account.

        msg = Message('Esito registrazione', sender=current_app.config['MAIL_SENDER'], 
                      recipients=[form.email.data])
        msg.body = "Registrazione avvenuta con successo!"
        mail.send(msg)

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



@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():

    class ResetPasswordRequestForm(FlaskForm):
        email = StringField(current_app.config["LABELS"]["email"], validators=[DataRequired(), Email()])
        submit = SubmitField(current_app.config["LABELS"]["request_password_reset"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_password_token()

            # Invio email.
            
            send_email(subject=current_app.config["LABELS"]["password_reset_mail"],
                       sender=current_app.config['MAIL_SENDER'],
                       recipients=[form.email.data], 
                       text_body=render_template('email/reset_password.txt',  user=user, token=token),
                       html_body=render_template('email/reset_password.html', user=user, token=token))

        flash('Controlla la tua email per le istruzioni per il reset della password')
        return redirect(url_for('auth.login'))

    return render_template('auth/password_reset_request.html', 
                           title=current_app.config["LABELS"]["password_reset"], 
                           form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    class ResetPasswordForm(FlaskForm):
        password = PasswordField('Password', validators=[DataRequired()])
        password2 = PasswordField(
            'Ripeti Password', validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField('Richiedi modifica password')


    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

