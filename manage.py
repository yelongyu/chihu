#!/usr/bin/env python

# -*- coding:utf-8 -*-

########### env need to set #################
# SECRET_KEY            ;avoid CSRF
# DATABASE              ;database URI
# MAIL_USERNAME         ;mail sender
# MAIL_PASSWORD         ;mail sender password
# MAIL_ADMIN            ;mail receiver
# FLASK_CONFIG          ;config
#############################################
import os

from app import create_app
from app import db

from app.models import User
from app.models import Role

from flask.ext.script import Manager
from flask.ext.script import Shell

from flask.ext.migrate import Migrate
from flask.ext.migrate import MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    ''' run the unit test '''
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()
