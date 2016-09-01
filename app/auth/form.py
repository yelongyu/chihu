# -*- encoding:utf-8 -*-

from flask.ext.wtf import Form

from wtforms import StringField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import SubmitField

from wtforms.validators import Required
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import Regexp
from wtforms.validators import EqualTo
from wtforms.validators import ValidationError

from ..models import User


# 登陆表单
class LoginForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[Required()])
    remember_me = BooleanField('保持登录状态')
    submit = SubmitField(u'登陆')


# 注册表单
class RegisterForm(Form):
    email = StringField('邮箱', validators=[Required(), Length(1, 64),
                        Email()])
    username = StringField('用户名', validators=[Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                        '用户名只能包含数字、字母、下划线！')])
    password = PasswordField('密码', validators=[Required(), \
             EqualTo('password2', message='两次输入的密码不匹配！')])
    password2 = PasswordField('请再次确认密码', validators=[Required()])
    submit = SubmitField('注册')

    # 自定义验证函数 validate_开头加字段名
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已注册！')
        
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用！')


# 密码修改表单
class ChangePasswordForm(Form):
    old_password = PasswordField('密码:', validators=[Required()])
    password = PasswordField('新密码:', validators=[Required(),
                    EqualTo('password2', message='Password must match')])
    password2 = PasswordField('请重新确认新密码:', validators=[Required()])
    submit = SubmitField('提交')


# 密码重置邮箱提交表单
class ResetPasswordRequestForm(Form):
    email = StringField('请输入账号邮箱:', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('提交')


# 密码重置表单
class ResetPasswordForm(Form):
    email = StringField('邮箱账号:', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('请输入新密码:', validators=[Required(),
                    EqualTo('password2', message='Password must match')])
    password2 = PasswordField('请确认新密码:', validators=[Required()])
    submit = SubmitField('提交')


# 邮箱修改表单
class ChangeEmailForm(Form):
    email = StringField('请输入新的邮件地址:', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('密码:', validators=[Required()])
    submit = SubmitField('提交:')


