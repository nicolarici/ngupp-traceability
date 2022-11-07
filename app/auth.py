from flask import Blueprint, render_template, url_for, current_app, redirect, flash, request
from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Regexp
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.extension import db, mail
from flask_mail import Message
from app.widgets import CustomPasswordField, CustomStringField
from flask import Markup


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
        email = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["email"] + "</strong>"), 
                                  validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                              Email(message=current_app.config["LABELS"]["email_error"]),
                                              Regexp(".*@giustizia\.it$", message=current_app.config["LABELS"]["mail_error_giustizia"])])
                                        
        password = CustomPasswordField(Markup("<strong>" + current_app.config["LABELS"]["password"] + "</strong>"), 
                                       validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                                   Regexp("^(?=.*[A-Za-z])(?=.*\d).{8,15}$", message=current_app.config["LABELS"]["password_error"])])

        confirm  = CustomPasswordField(Markup("<strong>" + current_app.config["LABELS"]["confirm_password"] + "</strong>"),
                                       validators=[EqualTo('confirm', message=current_app.config["LABELS"]["password_match_error"])])

        nome_ufficio = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["nome_ufficio_opz"] + "</strong>"))

        ufficio = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["ufficio"] + "</strong>"), 
                                    validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        submit = SubmitField(current_app.config["LABELS"]["registration"])


        def validate_email(self, email):

            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError(current_app.config["LABELS"]["email_alredy_used"])

            
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():

        nome_cognome = form.email.data.split("@")[0].split(".")

        nome = nome_cognome[0].capitalize()
        try:
            cognome = nome_cognome[1].capitalize()
        except:
            cognome = ""
            
        superuser = form.email.data == current_app.config["ADMIN_MAIL"]        

        user = User(nome=nome, cognome=cognome, email=form.email.data, ufficio=form.ufficio.data, nome_ufficio=form.nome_ufficio.data, superuser=superuser)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Invia e-mail di conferma account.

        if user:
            token = user.get_registration_token()
            
            send_email(subject=current_app.config["LABELS"]["confirm_registration"],
                       sender=current_app.config['MAIL_SENDER'],
                       recipients=[form.email.data], 
                       text_body=render_template('email/confirm_registration.txt',  user=user, token=token),
                       html_body=render_template('email/confirm_registration.html', user=user, token=token))

        flash(current_app.config["LABELS"]["registration_email_sent"], "info")

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', 
                           form=form, btn_map={"submit": "primary"})


@bp.route('/confirm_registration/<token>', methods=['GET', 'POST'])
def confirm_registration(token):

    user = User.verify_registration_token(token)

    if user is None:
        return redirect(url_for('index'))

    user.confirmed = True
    db.session.commit()

    flash(current_app.config["LABELS"]["registration_confirmed"], "success")
    return redirect(url_for('auth.login'))


@bp.route("/re_confirm_registration", methods=['GET', 'POST'])
def re_confirm_registration():

    class ReConfirmRegistrationForm(FlaskForm):
        email = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["email"] + "</strong>"), 
                                  validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                              Regexp(".*@giustizia\.it$", message=current_app.config["LABELS"]["mail_error_giustizia"]),
                                              Email()])
        submit = SubmitField(current_app.config["LABELS"]["reconfirm_registration"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ReConfirmRegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            if user.confirmed:
                flash(current_app.config["LABELS"]["user_alredy_confirmed"], "warning")
            
            else:     
                token = user.get_registration_token()

                # Invio email.
                
                send_email(subject=current_app.config["LABELS"]["confirm_registration"],
                        sender=current_app.config['MAIL_SENDER'],
                        recipients=[form.email.data], 
                        text_body=render_template('email/confirm_registration.txt',  user=user, token=token),
                        html_body=render_template('email/confirm_registration.html', user=user, token=token))

                flash(current_app.config["LABELS"]["registration_email_sent"], "info")
                return redirect(url_for('auth.login'))
                        
        else:
            flash(current_app.config["LABELS"]["wrong_email"], "danger")

    return render_template('auth/reconfirm_registration.html', 
                           form=form,
                           btn_map={"submit": "primary"})


@bp.route('/login', methods=['GET', 'POST'])
def login():

    class LoginForm(FlaskForm):
        email = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["email"] + "</strong>"), 
                                  validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                              Email(message=current_app.config["LABELS"]["email_error"])])
                                        
        password = CustomPasswordField(Markup("<strong>" + current_app.config["LABELS"]["password"] + "</strong>"), 
                                       validators=[DataRequired(message=current_app.config["LABELS"]["required"])])

        remember_me = BooleanField(current_app.config["LABELS"]["remember_me"])

        submit = SubmitField(current_app.config["LABELS"]["login"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash(current_app.config["LABELS"]["login_error"], "danger")
            return redirect(url_for('auth.login'))

        if not user.confirmed:
            return redirect(url_for('auth.re_confirm_registration'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('auth/login.html', 
                           form=form, btn_map={"submit": "primary"})


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():

    class ResetPasswordRequestForm(FlaskForm):
        email = CustomStringField(Markup("<strong>" + current_app.config["LABELS"]["email"] + "</strong>"), 
                                  validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                              Regexp(".*@giustizia\.it$", message=current_app.config["LABELS"]["mail_error_giustizia"]),
                                              Email()])
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

                flash(current_app.config["LABELS"]["password_reset_email_sent"], "info")
                return redirect(url_for('auth.login'))

    return render_template('auth/password_reset_request.html', 
                           form=form, btn_map={"submit": "primary"})


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    class ResetPasswordForm(FlaskForm):
        password = CustomPasswordField(Markup("<strong>" + current_app.config["LABELS"]["password"] + "</strong>"),
                                       validators=[DataRequired(message=current_app.config["LABELS"]["required"]),
                                       Regexp("^(?=.*[A-Za-z])(?=.*\d).{8,15}$", message=current_app.config["LABELS"]["password_error"])])
                                       
        confirm =  CustomPasswordField(Markup("<strong>" + current_app.config["LABELS"]["ripeti_password"] + "</strong>"),
                                         validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                                     EqualTo('password', message=current_app.config["LABELS"]["password_match_error"])])
        
        submit = SubmitField(current_app.config["LABELS"]["modify_password"])


    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash(current_app.config["LABELS"]["password_reset_success"], "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, btn_map={"submit": "primary"})
