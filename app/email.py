from flask.ext.mail import Message
from threading import Thread
from flask import current_app, render_template
from . import mail

import os

def send_mail_async(app, msg):
   with app.app_context():
        mail.send(msg) 

def send_mail(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject, sender=os.environ.get('MAIL_USERNAME'), recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    thr = Thread(target=send_mail_async, args=[app, msg])
    thr.start()

    return thr
