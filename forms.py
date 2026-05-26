from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional

class AddRunnerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional()])

    referral = SelectField(
        "How did you hear about us?",
        choices=[
            ("instagram", "Instagram"),
            ("friend", "Friend"),
            ("facebook", "Facebook"),
            ("event", "Event"),
            ("google", "Google Search"),
            ("other", "Other")
        ],
        validators=[Optional()]
    )
    emoji = SelectField(
    "Emoji",
    choices=[
        ("🏃", "🏃 Runner"),
        ("🔥", "🔥 Hot Streak"),
        ("🌟", "🌟 Star"),
        ("🐢", "🐢 Turtle"),
        ("⚡", "⚡ Speed"),
        ("🍀", "🍀 Lucky"),
        ("💪", "💪 Strong")
    ]
)


    waiver_signed = StringField("Waiver Signed")
    submit = SubmitField("Add Runner")
