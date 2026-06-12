from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from forms import AddRunnerForm
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///runclub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------
# MODELS
# ---------------------------------------------------------

class Runner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    referral = db.Column(db.String(120))
    emoji = db.Column(db.String(10))
    waiver_signed = db.Column(db.Boolean, default=False)
    waiver_date = db.Column(db.Date)
    device_token = db.Column(db.String(255))  # NEW: secure device token


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    runner_id = db.Column(db.Integer, db.ForeignKey('runner.id'))
    date = db.Column(db.Date, default=date.today)
    runner = db.relationship('Runner', backref='attendance')

# ---------------------------------------------------------
# STREAK CALCULATION
# ---------------------------------------------------------

def calculate_streak(dates):
    if not dates:
        return 0

    dates = sorted(set(dates), reverse=True)
    streak = 1
    today = date.today()

    if dates[0] != today:
        return 0

    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] - timedelta(days=1):
            streak += 1
        else:
            break

    return streak

# ---------------------------------------------------------
# HOME / QUICK CHECK-IN LIST
# ---------------------------------------------------------

@app.route('/')
def index():
    today = date.today()
    checked_in = Attendance.query.filter_by(date=today).all()
    runners = Runner.query.order_by(Runner.name).all()
    return render_template("index.html", checked_in=checked_in, runners=runners)

# ---------------------------------------------------------
# DEVICE VALIDATION (Option B)
# ---------------------------------------------------------

@app.route('/validate_device/<int:runner_id>', methods=['POST'])
def validate_device(runner_id):
    runner = Runner.query.get_or_404(runner_id)
    provided_token = request.json.get("token")

    # If runner has no token yet → issue one
    if not runner.device_token:
        raw_token = secrets.token_hex(16)
        runner.device_token = generate_password_hash(raw_token)
        db.session.commit()
        return jsonify({"status": "new", "token": raw_token})

    # If runner has a token → validate
    if provided_token and check_password_hash(runner.device_token, provided_token):
        return jsonify({"status": "valid"})

    return jsonify({"status": "invalid"}), 403

# ---------------------------------------------------------
# QUICK CHECK-IN ROUTE
# ---------------------------------------------------------

@app.route('/quick_checkin/<int:runner_id>', methods=['POST'])
def quick_checkin(runner_id):
    today = date.today()
    already = Attendance.query.filter_by(runner_id=runner_id, date=today).first()

    if not already:
        db.session.add(Attendance(runner_id=runner_id, date=today))
        db.session.commit()

    return jsonify({"status": "checked_in"})

# ---------------------------------------------------------
# SEARCH + CHECK-IN PAGE
# ---------------------------------------------------------

@app.route('/checking', methods=['GET'])
def checking():
    q = request.args.get('q', '').strip()
    runners = []

    if q:
        runners = Runner.query.filter(Runner.name.ilike(f"%{q}%")).all()

    return render_template("checking.html", runners=runners, query=q)

@app.route('/checkin/<int:runner_id>', methods=['POST'])
def checkin_runner(runner_id):
    today = date.today()

    already = Attendance.query.filter_by(runner_id=runner_id, date=today).first()
    if not already:
        new_checkin = Attendance(runner_id=runner_id, date=today)
        db.session.add(new_checkin)
        db.session.commit()

    return redirect(url_for('checking'))

# ---------------------------------------------------------
# ADD RUNNER PAGE
# ---------------------------------------------------------

@app.route('/runners', methods=['GET', 'POST'])
def runners():
    form = AddRunnerForm()

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        referral = request.form.get("referral")
        emoji = request.form.get("emoji")
        waiver_signed = request.form.get("waiver_signed") == "true"

        new_runner = Runner(
            name=name,
            phone=phone,
            referral=referral,
            emoji=emoji,
            waiver_signed=waiver_signed,
            waiver_date=date.today() if waiver_signed else None
        )

        db.session.add(new_runner)
        db.session.commit()

        return redirect(url_for('runners'))

    all_runners = Runner.query.order_by(Runner.name).all()
    return render_template("runners.html", form=form, runners=all_runners)

# ---------------------------------------------------------
# REWARDS DASHBOARD
# ---------------------------------------------------------

@app.route('/rewards')
def rewards():
    all_runners = Runner.query.all()
    today = date.today()

    # Monthly leaderboard
    first_of_month = today.replace(day=1)
    monthly_attendance = Attendance.query.filter(Attendance.date >= first_of_month).all()

    monthly_counts = {}
    for a in monthly_attendance:
        monthly_counts[a.runner_id] = monthly_counts.get(a.runner_id, 0) + 1

    if monthly_counts:
        top_runner_id = max(monthly_counts, key=monthly_counts.get)
        top_runner = Runner.query.get(top_runner_id)
        top_runner_name = top_runner.name
        top_runner_count = monthly_counts[top_runner_id]
    else:
        top_runner_name = None
        top_runner_count = 0

    # Build heatmap data
    all_attendance = Attendance.query.all()
    attendance_by_date = {}

    for a in all_attendance:
        attendance_by_date[a.date] = attendance_by_date.get(a.date, 0) + 1

    if attendance_by_date:
        min_date = min(attendance_by_date.keys())
        max_date = max(attendance_by_date.keys())
    else:
        min_date = today
        max_date = today

    timeline = []
    current = min_date
    while current <= max_date:
        timeline.append({
            "date": current,
            "count": attendance_by_date.get(current, 0)
        })
        current += timedelta(days=1)

    # Runner-specific data
    runners_data = []
    for r in all_runners:
        dates = [a.date for a in Attendance.query.filter_by(runner_id=r.id).all()]
        streak = calculate_streak(dates)
        total_runs = len(dates)

        milestones = []
        if total_runs >= 10: milestones.append("10 Runs")
        if total_runs >= 25: milestones.append("25 Runs")
        if total_runs >= 50: milestones.append("50 Runs")
        if total_runs >= 100: milestones.append("100 Runs")

        runners_data.append({
            "name": r.name,
            "emoji": r.emoji,
            "streak": streak,
            "total_runs": total_runs,
            "milestones": milestones
        })

    return render_template(
        "rewards.html",
        runners=runners_data,
        timeline=timeline,
        top_runner_name=top_runner_name,
        top_runner_count=top_runner_count
    )

# ---------------------------------------------------------
# INIT
# ---------------------------------------------------------

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
