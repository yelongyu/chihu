import os

basedir = os.path.abspath(os.path.dirname('__file__'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '!@#^&$#@%#$FTEWQ"%#@!39v8'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE') or \
                            'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE') or \
                            'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE') or \
                            'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

config = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
}
