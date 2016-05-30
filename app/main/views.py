from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request

from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_mail

import os

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    users = User.query.all()
    if form.validate_on_submit():
        message = form.message.data
        name = form.name.data
        old_name = session.get('name')
        if old_name != None and old_name != form.name.data:
            flash('Seems You Have Changed Your Name.')
            send_mail(os.environ.get('MAIL_ADMIN'), 'New User', 'mail/mail', username=name)
        else:
            flash('Welcome Back.')
        form.name.data = ''
        form.message.data = ''
        session['name'] = name
        user_name = User.query.filter_by(username=name).first()

        if user_name == None:
            user = User(username=name, 
                        message=message)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            flash('User Already Exist!')
            session['known'] = True
        return redirect(url_for('main.index'))
    return render_template('index.html',
                            form=form,
                            name=session.get('name'),
                            users=users, 
                            known=session.get('known', False))

@main.route('/login', methods=['GET', 'POST'])
def login():
    print 'request.method = %s' % request.method
    if request.method == 'POST':
        name = request.form['name']
        passwd = request.form['password']
        print 'name = %s' % name
        print 'passwd = %s' % passwd
        username = User.query.filter_by(username=name).first()
        if username == None:
            flash('login fail..')
            return render_template('login.html')
        else:
            flash('login success..')
            return render_template('index.html')
    return render_template('login.html')


@main.route('/user/<name>')
def user(name):
	return render_template('user.html', name=name)
