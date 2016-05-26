#!/usr/bin/env python

# -*- coding:utf-8 -*-

########### env need to set #################
# SECRET_KEY            ;avoid CSRF
# DATABASE              ;database URI
# MAIL_USERNAME         ;mail sender
# MAIL_PASSWORD         ;mail sender password
# MAIL_ADMIN            ;mail receiver
#############################################

''' chihu '''

from flask import Flask, render_template, request, session, make_response
from flask import abort, flash, redirect, url_for

from flask.ext.script import Manager, Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message

import os.path
import time
from threading import Thread

basedir = os.path.abspath(os.path.dirname(__file__))

from datetime import datetime

app = Flask(__name__)
app.debug = True

app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY') # avoid CSRF
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE')
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = True

app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

def send_mail(to, subject, template, **kwargs):
    msg = Message(subject, sender=os.environ.get('MAIL_USERNAME'), recipients=[to])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html', **kwargs)

    thr = Thread(target=send_mail_async, args=[app, msg])
    thr.start()

    return thr

def send_mail_async(app, msg):
    with app.app_context():
        mail.send(msg)

class NameForm(Form):
    name = StringField('name:', validators=[Required()])
    message = TextAreaField('message:')
    submit = SubmitField('Submit')


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    message = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    users = User.query.all()
    if form.validate_on_submit():
        message = form.message.data
        name = form.name.data
        old_name = session.get('name')
        if old_name != None and old_name != form.name.data:
            flash('Seems You Have Changed Your Name.')
            send_mail(os.environ.get('MAIL_ADMIN'), 'New User', 'mail/mail')
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
        return redirect(url_for('index'))
    return render_template('index.html',
                            form=form,
                            name=session.get('name'),
                            users=users, 
                            known=session.get('known', False))

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/user/<name>')
def user(name):
	return render_template('user.html', name=name)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html')
	
@app.errorhandler(500)
def page_not_found(e):
	return render_template('500.html')


if __name__ == '__main__':
	manager.run()
