from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired

class TimeSeriesForm(FlaskForm):
    table = SelectField('Select Data to Analyze', validators=[DataRequired()])
    restrictions = SelectMultipleField('Restrictions')
    prompt = TextAreaField('Analysis Prompt')
