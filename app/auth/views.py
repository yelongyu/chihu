#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# import style learn from sqlmap source code
# import one by one

# flask built in
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash

from . import auth

# form
from .form import LoginForm                     # 登陆
from .form import RegisterForm                  # 注册
from .form import ChangePasswordForm            # 修改密码
from .form import ResetPasswordRequestForm      # 重置密码输入邮箱
from .form import ResetPasswordForm             # 重置密码
from .form import ChangeEmailForm               # 修改邮箱

# 管理已登录用户的用户会话
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import login_required     # 保护路由
from flask.ext.login import current_user

from ..models import User

from .. import db
from ..email import send_mail

# fix UnicodeEncoding Error
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


# 用户登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('登陆成功!')
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('用户名或密码错误！')
    return render_template('auth/login.html', form=form)

# 用户注销
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('注销成功！')
    return redirect(url_for('main.index'))

# 用户注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_mail(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        flash('注册成功！请登录。')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)
    

# 邮箱验证
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('邮箱确认成功！请登录。')
    else:
        flash('邮箱确认链接有误或已失效！请重新确认。')
    return redirect(url_for('main.index'))

# 未确认邮箱用户的请求统一重定向到固定页面
@auth.before_app_request   # 程序全局钩子
def before_request():
    if current_user.is_authenticated:
            current_user.ping()  # 更新用户的上次登录时间
            if not current_user.confirmed \
                    and request.endpoint[:5] != 'auth.' \
                    and request.endpoint != 'static':
                return redirect(url_for('auth.unconfirmed'))

# 未确认邮箱用户
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

# 重新发送确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认邮件已经发送到您的邮箱，请登录邮箱确认。')
    return redirect(url_for('main.index'))


# 密码修改
@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('密码修改成功！')
            return redirect(url_for('main.index'))
        else:
            flash('密码有误，请重新输入！')
            form.old_password.data = ''
            form.password.data = ''
            form.password2.data = ''
    return render_template('auth/change_password.html', form=form)

# 密码重置邮件发送
@auth.route('/reset_password', methods=['GET', 'POST'])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('未找到该注册邮箱！新用户？请注册登陆。')
            return redirect(url_for('auth.login'))
        token = user.generate_reset_password_token()
        send_mail(form.email.data, '密码重置确认', 'auth/email/reset_password_confirm', user=user, token=token)
        flash('一封确认邮件已发送到您的邮箱，请登录邮箱并确认。')
    return render_template('auth/reset_password_request.html', form=form)

# 密码重置
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect('main.index')
    form = ResetPasswordForm()
    if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is None:
                flash('邮箱错误!请重新输入！')
                form.email.data = ''
                return redirect(url_for('auth.reset_password'))
            else:
                if user.reset_password(token, form.password.data):
                    flash('密码重置成功！请重新登陆！')
                else:
                    flash('邮箱验证失败！请重新验证！')
                    return redirect(url_for('auth.request_reset_password'))
                return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


# 邮箱更改验证
@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            token = current_user.generate_change_email_token(form.email.data)
            send_mail(form.email.data, '修改邮箱确认', 'auth/email/change_email_confirm', user=current_user, token=token)
            flash('确认邮件已发送到该新邮箱，请登录新邮箱进行验证。')
        else:
            flash('密码错误，请重新输入!')
    return render_template('auth/change_email.html', form=form)

# 邮箱更改
@auth.route('/change_email/<token>')
@login_required
def change_email_confirm(token):
    if current_user.change_email(token):
        flash('邮箱地址更新成功!')
    else:
        flash('链接已失效，请重新验证!')
    return redirect(url_for('main.index'))