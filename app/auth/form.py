from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, \
    ValidationError

from ..models import User


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), 
                        Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegisterForm(Form):
    email = StringField('email', validators=[Required(), Length(1, 64), 
                        Email()])
    username = StringField('username', validators=[Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                        'Usernames must have only letters, ' \
                        'numbers, dots or underscores')])
    password = PasswordField('password', validators=[Required(), \
             EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('confirm password', validators=[Required()])
    
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already register.')
        
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

    def validate_password(self, field):
        if '1' in field.data:
            raise ValidationError('Password can not contain 1! so, this is \
                                    just a test.')


class ChangePasswordForm(Form):
    old_password = StringField('old password:', validators=[Required()])
    new_password = PasswordField('new password:', validators=[Required(), 
                    EqualTo('new_password2', message='Password must match')])
    new_password2 = PasswordField('confirm password:', validators=[Required()])

    submit = SubmitField('Submit')


class ChangeProfileForm(Form):
    username = StringField('User Name:', validators=[Length(0, 64)])
    location = StringField('Location:', validators=[Length(0, 64)])
    about_me = StringField('About Me:', validators=[Length(0, 256)])
    submit = SubmitField('Update')


class ResetPasswordForm(Form):
    email = StringField('Email:', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Submit:')