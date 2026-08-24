from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class AddRunnerForm(FlaskForm):
    # Basic info
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional()])

    # Referral source
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

    # Emoji avatar
    emoji = SelectField(
        "Choose an Emoji Avatar",
        choices=[
            ("🏃", "🏃 Runner"),
            ("🏃‍♀️", "🏃‍♀️ Runner (Female)"),
            ("🏃‍♂️", "🏃‍♂️ Runner (Male)"),
            ("🔥", "🔥 Hot Streak"),
            ("🌟", "🌟 Star"),
            ("🐢", "🐢 Turtle"),
            ("⚡", "⚡ Speed"),
            ("🍀", "🍀 Lucky"),
            ("💪", "💪 Strong"),
            ("🦾", "🦾 Power"),
            ("🚀", "🚀 Rocket"),
            ("🎯", "🎯 On Target"),
            ("🏅", "🏅 Medal"),
            ("🥇", "🥇 Champion"),
            ("🌈", "🌈 Rainbow"),
            ("☀️", "☀️ Sunshine"),
            ("🌙", "🌙 Night Runner"),
            ("🧠", "🧠 Mindset"),
            ("❤️", "❤️ Heart"),
            ("🤝", "🤝 Team Player")
        ],
        validators=[Optional()]
    )

    # Shoe brand
    shoe_brand = SelectField(
        "Shoe Brand",
        choices=[
            ("nike", "Nike"),
            ("adidas", "Adidas"),
            ("brooks", "Brooks"),
            ("asics", "ASICS"),
            ("saucony", "Saucony"),
            ("hoka", "HOKA"),
            ("newbalance", "New Balance"),
            ("mizuno", "Mizuno"),
            ("oncloud", "On Cloud"),
            ("altra", "Altra"),                           
            ("other", "Other")
        ]
    )

    # Waiver
    waiver_signed = BooleanField("Waiver Signed")

    # Submit button
    submit = SubmitField("Add Runner")
