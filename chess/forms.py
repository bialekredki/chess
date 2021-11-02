from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField, RadioField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from wtforms.widgets.core import Select
from chess.models import User, ChessBoardTheme


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remeber me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use another username')

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use another email')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There\' no account associated with this email')

class SettingsForm(FlaskForm):
    is_private = RadioField('Account visibility', choices=[('public','Public'), ('private','Private')], validators=[DataRequired()])
    new_password = PasswordField('New password')
    confirm_new_password = PasswordField('Confirm new password')
    name = StringField('Your name')
    chess_theme = SelectField('Theme', choices=[(x.name,x.name) for x in ChessBoardTheme.query.all()])
    password = PasswordField('Confirm password')
    submit = SubmitField('Accept changes')

    def change_password(self)->bool:
        return True if self.new_password.data == self.confirm_new_password.data and self.new_password.data != '' else False
