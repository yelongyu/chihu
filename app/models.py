from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

from flask.ext.login import UserMixin, AnonymousUserMixin

from . import login_manager
import os
from datetime import datetime
import hashlib
from flask import request

from markdown import markdown
import bleach


# fix the UnicodeEncodingError.
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Integer, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email == os.environ.get('MAIL_ADMIN'):
            self.role = Role.query.filter_by(permissions=0xff).first()
        else:
            self.role = Role.query.filter_by(default=True).first()

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # flash last_seen every time when user send a request
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:  
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
            
        return True

    def gravatar(self, size=50, default='idention', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}'.format(url=url, hash=hash, size=size)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
                u = User(email=forgery_py.internet.email_address(),
                         username=forgery_py.internet.user_name(True),
                         password=forgery_py.lorem_ipsum.word(),
                         confirmed=True,
                         location=forgery_py.address.city(),
                         about_me=forgery_py.lorem_ipsum.sentence(),
                         member_since=forgery_py.date.date(True))
                db.session.add(u)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def ping(self):
        pass

login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    favor = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_abtract = db.Column(db.Text)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentence(),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
                        'ul', 'pre', 'strong', 'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                       tags=allowed_tags, strip=True))
        target.body_abstract = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                        tags=['p'], strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)


class Click(db.Model):
    __tablename__ = 'click_count'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    url_name = db.Column(db.String(64), unique=True)
    click_count = db.Column(db.Integer)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class SiteData(db.Model):
    __tablename__ = 'sitedata'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    visitor_count = db.Column(db.Integer, default=0)




# 2016.07.09 22:25 visitor statistic
class StatisticVisitor(db.Model):
    __tablename__ = 'statistic_visitor'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    last_count = db.Column(db.DateTime, index=True)      # last count date
    referred = db.Column(db.Text, default='No Referred')
    agent = db.Column(db.String(64))
    platform = db.Column(db.String(64))
    version = db.Column(db.String(64))
    ip = db.Column(db.String(64))
    hits = db.Column(db.Integer, default=0)

# 2016.07.21 machine statistic
class Machine(db.Model):
    __tablename__ = 'machine_statistic'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    type = db.Column(db.String(64))
    company = db.Column(db.String(64))
    version = db.Column(db.String(64))
    timestamp = db.Column(db.String(64))
    userid = db.Column(db.String(64))
    userpasswd = db.Column(db.String(64))
    netcode = db.Column(db.String(64))
    login_time = db.Column(db.DateTime, index=True)
    ip = db.Column(db.String(64))
    localip = db.Column(db.String(64))
    gateway = db.Column(db.String(64))
    wlanmac = db.Column(db.String(64))
    wlanssid = db.Column(db.String(64))
    wlanpasswd = db.Column(db.String(64))
    webkey = db.Column(db.String(64))
    openid = db.Column(db.String(64))

