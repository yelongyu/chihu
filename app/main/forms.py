# -*- encoding: utf-8 -*-

from flask.ext.wtf import Form

from flask.ext.pagedown.fields import PageDownField

from wtforms.validators import Required
from wtforms.validators import Length
from wtforms.validators import Regexp

from wtforms import StringField
from wtforms import SubmitField
from wtforms import BooleanField
from wtforms import SelectField
from wtforms import ValidationError

from ..models import User
from ..models import Role
from ..models import Category

# 帖子发表提交表单
class PostForm(Form):
    title = StringField('标题:', validators=[Required()])
    category = SelectField('分类:', coerce=int)
    body = PageDownField('内容:', validators=[Required()])
    submit = SubmitField('发表')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name) for category in Category.query.order_by(Category.id).all()]

# 分类增加表单
class CategoryForm(Form):
    category = StringField('新增分类:')
    submit = SubmitField('提交')

# 登陆用户评论提交表单
class CommentForm(Form):
    body = PageDownField('评论:', validators=[Required()])
    submit = SubmitField('发表')

# 访客评论提交表单
class VisitorCommentForm(Form):
    name = StringField('用户名:', validators=[Required()])
    body = PageDownField('评论:', validators=[Required()])
    submit = SubmitField('发表')

# 普通用户资料编辑表单
class EditProfileForm(Form):
    username = StringField('用户名:', validators=[Length(0, 64)])
    location = StringField('城市:', validators=[Length(0, 64)])
    about_me = StringField('关于:', validators=[Length(0, 256)])
    submit = SubmitField('提交')

# 管理员用户资料编辑表单
class EditProfileAdminForm(Form):
    email = StringField('邮箱:', validators=[Required(), Length(1, 64)])
    username = StringField('用户名:', validators=[Required(), Length(1, 64),
                                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                      '用户名必须只包含字母、数字、点和下划线')])
    realname = StringField('真实姓名:', validators=[Length(0, 64)])
    confirmed = BooleanField('已验证:')
    role = SelectField('用户角色:', coerce=int)
    location = StringField('城市:', validators=[Length(0, 64)])
    about_me = StringField('关于:', validators=[Length(0, 256)])
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已注册！')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已占用!')