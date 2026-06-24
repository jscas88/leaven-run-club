from flask import Flask, render_template, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from models import db, Runner, Attendance
from forms import AddRunnerForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///runclub.db'
app.config['SECRET_KEY'] = 'secretkey'
db.init_app(app)


# -----------------------------
# NEXT RUN CALCULATION (Friday 6:30 PM)
# -----------------------------
def get_next_run():
    now = datetime.now()
    # Friday = 4
    days_ahead = (4 - now.weekday()) % 7
    next_run = now + timedelta(days=days_ahead)
    next_run = next_run.replace(hour=18, minute=30, second=0, microsecond=0)

    if next_run < now:
        next_run += timedelta(days=7)

    return next_run


# -----------------------------
# 4-WEEK CALENDAR GENERATOR
# -----------------------------
def get_four_week_calendar(start_date=None):
    if not start_date:
        start_date = date.today()

    # Find Sunday of current week
    start_of_week = start_date - timedelta(days=start_date.weekday() + 1 if start_date.weekday() < 6 else 0)

    days = [start_of_week + timedelta(days=i) for i in range(28)]
    weeks = [days[i:i+7] for i in range(0, 28, 7)]
    return weeks


# -----------------------------
# HOME / LANDING PAGE
# -----------------------------
@app.route("/")
def index():
    next_run = get_next_run()
    weeks = get_four_week_calendar()

    fridays = [d for week in weeks for d in week if d.weekday() == 4]

    return render_template(
        "index.html",
        next_run=next_run,
        weeks=weeks,
        fridays=fridays,
        date=date
    )


# -----------------------------
# CHECK-IN PAGE (GRID + BADGES + CODE)
# -----------------------------
@app.route("/checking", methods=["GET"])
def checking():
    today = date.today()
    runners = Runner.query.order_by(Runner.name.asc()).all()

    runner_data = []
    for r in runners:
        checked_today = Attendance.query.filter_by(runner_id=r.id, date=today).first() is not None

        # Last 4 digits of phone for verification
        last4 = (r.phone[-4:] if r.phone and len(r.phone) >= 4 else "0000")

        runner_data.append({
            "id": r.id,
            "name": r.name,
            "emoji": r.emoji or "🏃",
            "last4": last4,
            "checked_today": checked_today
        })

    return render_template("checking.html", runners=runner_data)


# -----------------------------
# AJAX CHECK-IN ENDPOINT
# -----------------------------
@app.route("/checkin_runner/<int:runner_id>", methods=["POST"])
def checkin_runner(runner_id):
    runner = Runner.query.get_or_404(runner_id)
    today = date.today()

    exists = Attendance.query.filter_by(runner_id=runner.id, date=today).first()
    if not exists:
        entry = Attendance(runner_id=runner.id, date=today)
        db.session.add(entry)
        db.session.commit()

    return jsonify({"success": True})


# -----------------------------
# ADD RUNNER PAGE
# -----------------------------
@app.route("/runners", methods=["GET", "POST"])
def runners_page():
    form = AddRunnerForm()
    runners = Runner.query.order_by(Runner.name.asc()).all()

    if form.validate_on_submit():
        new_runner = Runner(
            name=form.name.data,
            phone=form.phone.data,
            referral=form.referral.data,
            emoji=form.emoji.data,
            waiver_signed=form.waiver_signed.data
        )
        db.session.add(new_runner)
        db.session.commit()

        # Set toast flag
        session["new_runner_added"] = True

        return redirect("/checking")

    return render_template("runners.html", form=form, runners=runners)



# -----------------------------
# REWARDS PAGE
# -----------------------------
@app.route("/rewards")
def rewards():
    runners = Runner.query.all()
    attendance = Attendance.query.all()
    return render_template("rewards.html", runners=runners, attendance=attendance)


# -----------------------------
# RUN APP
# -----------------------------


@app.route("/clear_new_runner_flag", methods=["POST"])
def clear_new_runner_flag():
    session.pop("new_runner_added", None)
    return jsonify({"cleared": True})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
