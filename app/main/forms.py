from flask.ext.wtf import Form
from wtforms.validators import Required
from wtforms import StringField, TextAreaField, SubmitField

class NameForm(Form):
    name = StringField('name:', validators=[Required()])
    message = TextAreaField('message:')
    submit = SubmitField('Submit')


