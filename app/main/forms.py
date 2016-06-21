from flask.ext.wtf import Form
from wtforms.validators import Required
from wtforms import StringField, TextAreaField, SubmitField


class PostForm(Form):
    title = StringField('Title:', validators=[Required()])
    body = TextAreaField('Post:')
    submit = SubmitField('Submit')


