from flask import Blueprint, render_template, url_for, current_app, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


bp = Blueprint('auth', __name__, url_prefix='/auth')

# Login view

@bp.route('/register', methods=('GET', 'POST'))
def register():

    class LoginForm(FlaskForm):
        email = StringField(current_app.config["LABELS"]["email"], 
                            validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                        Email(message=current_app.config["LABELS"]["email_error"])])
                                        
        password = PasswordField(current_app.config["LABELS"]["password"], 
                                validators=[DataRequired(message=current_app.config["LABELS"]["required"]), 
                                            EqualTo('confirm', 
                                            message=current_app.config["LABELS"]["password_error"])])

        confirm  = PasswordField(current_app.config["LABELS"]["confirm_password"])

        submit = SubmitField(current_app.config["LABELS"]["registration"])


    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for('index'))

    return render_template('auth/register.html', 
                           title=current_app.config["LABELS"]["registration_title"], 
                           form=form)
