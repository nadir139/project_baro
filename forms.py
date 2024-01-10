# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class JobForm(FlaskForm):
    title = StringField('Job Title')
    image_url = StringField('Image URL')
    submit = SubmitField('Add Job')
