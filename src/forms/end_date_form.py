from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField
from wtforms.validators import DataRequired
from datetime import date

class RestrictionForm(FlaskForm):
    end_date = DateField(
        'Show restrictions up to:',
        validators=[DataRequired()],
        default=date(2021, 6, 15),
        render_kw={"min": "2020-01-01", "max": "2022-12-31"}
    )
    submit = SubmitField('Update')
