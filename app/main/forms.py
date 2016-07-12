from flask.ext.wtf import Form
from wtforms.validators import Required
from wtforms import StringField, TextAreaField, SubmitField
from flask.ext.pagedown.fields import PageDownField


class PostForm(Form):
    title = StringField('Title:', validators=[Required()])
    body = PageDownField('Post:', validators=[Required()])
    submit = SubmitField('Submit')


