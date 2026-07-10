from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Runner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    referral = db.Column(db.String(50))
    emoji = db.Column(db.String(10))
    shoe_brand = db.Column(db.String(50))
    waiver_signed = db.Column(db.Boolean, default=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    runner_id = db.Column(db.Integer, db.ForeignKey('runner.id'))
    date = db.Column(db.Date)
    verified = db.Column(db.Boolean, default=False)

    runner = db.relationship("Runner", backref="attendances")

