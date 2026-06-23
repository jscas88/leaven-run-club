from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class AddRunnerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional()])

    referral = SelectField(
        "How did you hear about us?",
        choices=[
            ("facebook", "Facebook"),
            ("instagram", "Instagram"),
            ("friend", "Friend"),
            ("other", "Other")
        ],
        validators=[Optional()]
    )

    emoji = SelectField(
        "Choose an Emoji Avatar",
        choices=[
            ("🏃", "🏃 Runner"),
            ("🔥", "🔥 Hot Streak"),
            ("🌟", "🌟 Star"),
            ("🐢", "🐢 Turtle"),
            ("⚡", "⚡ Speed"),
            ("🍀", "🍀 Lucky"),
            ("💪", "💪 Strong")
        ],
        validators=[Optional()]
    )

    waiver_signed = BooleanField("Waiver Signed")
    submit = SubmitField("Add Runner")
