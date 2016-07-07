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
from app import create_app, db
from app.models import User, Role
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
print 'FLASK CONFIG = %s' % os.environ.get('FLASK_CONFIG', 'Not found!')

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
