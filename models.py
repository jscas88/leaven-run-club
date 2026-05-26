from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Runner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    referral = db.Column(db.String(120))

    join_date = db.Column(db.Date, default=date.today)
    waiver_signed = db.Column(db.Boolean, default=False)
    waiver_date = db.Column(db.Date)

    # ⭐ NEW — Emoji avatar
    emoji = db.Column(db.String(10))

    attendance = db.relationship('Attendance', backref='runner', lazy=True)



class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    runner_id = db.Column(db.Integer, db.ForeignKey('runner.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
