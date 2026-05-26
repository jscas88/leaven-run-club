from flask import Flask, render_template, redirect, url_for, request, session
from datetime import date, datetime, timedelta
from models import db, Runner, Attendance
from forms import AddRunnerForm
import requests

# ─────────────────────────────────────────────
#  STREAK CALCULATION
# ─────────────────────────────────────────────
def calculate_streak(dates):
    if not dates:
        return 0

    dates = sorted(dates, reverse=True)
    streak = 1
    today = datetime.today().date()

    if dates[0] < today - timedelta(days=1):
        return 0

    for i in range(1, len(dates)):
        if dates[i] == dates[i-1] - timedelta(days=1):
            streak += 1
        else:
            break

    return streak


# ─────────────────────────────────────────────
#  FLASK APP CONFIG
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///runclub.db'
db.init_app(app)

with app.app_context():
    db.create_all()

ADMIN_PIN = "0645"


# ─────────────────────────────────────────────
#  GOOGLE SHEETS SYNC
# ─────────────────────────────────────────────
GOOGLE_SHEET_WEBHOOK = "YOUR_WEBHOOK_URL_HERE"

def sync_full_dataset():
    runners = Runner.query.all()

    runner_payload = []
    for r in runners:
        attendance = Attendance.query.filter_by(runner_id=r.id).all()
        dates = [a.date for a in attendance]
        streak = calculate_streak(dates)

        runner_payload.append({
            "id": r.id,
            "name": r.name,
            "phone": r.phone,
            "referralSource": r.referral,
            "joinDate": str(r.join_date) if r.join_date else "",
            "totalRuns": len(dates),
            "lastRun": str(max(dates)) if dates else "",
            "activeStreak": streak,
            "waiverSigned": r.waiver_signed,
            "waiverDate": str(r.waiver_date) if r.waiver_date else ""
        })

    all_dates = sorted({a.date for a in Attendance.query.all()})
    total_runners = len(runners)

    session_payload = []
    for d in all_dates:
        day_attendance = Attendance.query.filter_by(date=d).all()
        checked_in_ids = [a.runner_id for a in day_attendance]
        attendance_pct = round((len(day_attendance) / total_runners) * 100, 1) if total_runners else 0

        session_payload.append({
            "date": str(d),
            "checkedInCount": len(day_attendance),
            "totalRunners": total_runners,
            "attendancePct": attendance_pct,
            "notes": "",
            "checkedIn": checked_in_ids
        })

    payload = {
        "runners": runner_payload,
        "sessions": session_payload,
        "syncedAt": datetime.now().isoformat()
    }

    try:
        requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        print("Synced to Google Sheets")
    except Exception as e:
        print("Sync failed:", e)


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    today = date.today()
    checked_in = Attendance.query.filter_by(date=today).all()
    runners = Runner.query.all()
    return render_template('index.html', checked_in=checked_in, runners=runners)


@app.route('/runners', methods=['GET', 'POST'])
def runners():
    form = AddRunnerForm()

    if request.method == "POST":
        waiver_value = request.form.get("waiver_signed") == "true"

        new_runner = Runner(
            name=form.name.data,
            phone=form.phone.data,
            referral=form.referral.data,
            join_date=date.today(),
            waiver_signed=waiver_value,
            waiver_date=date.today() if waiver_value else None,
            emoji=form.emoji.data
        )

        db.session.add(new_runner)
        db.session.commit()
        sync_full_dataset()

        return redirect(url_for('runners'))

    all_runners = Runner.query.all()
    return render_template('runners.html', form=form, runners=all_runners)


@app.route('/checking', methods=['GET'])
def checking():
    q = request.args.get("q", "")
    runners = Runner.query.filter(Runner.name.ilike(f"%{q}%")).all() if q else []
    return render_template("checking.html", runners=runners, query=q)


@app.route('/checkin_runner/<int:runner_id>', methods=['POST'])
def checkin_runner(runner_id):
    today = date.today()
    exists = Attendance.query.filter_by(runner_id=runner_id, date=today).first()

    if not exists:
        entry = Attendance(runner_id=runner_id, date=today)
        db.session.add(entry)
        db.session.commit()
        sync_full_dataset()

    return redirect(url_for('checking'))


@app.route('/rewards')
def rewards():
    all_runners = Runner.query.all()
    runners_with_streaks = []

    for r in all_runners:
        dates = [a.date for a in Attendance.query.filter_by(runner_id=r.id).all()]
        streak = calculate_streak(dates)

        runners_with_streaks.append({
            "name": r.name,
            "emoji": r.emoji,
            "streak": streak
        })

    return render_template('rewards.html', runners=runners_with_streaks)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == "POST":
        if request.form.get("pin") == ADMIN_PIN:
            session["admin"] = True
            return redirect(url_for("runners"))
    return render_template("admin_login.html")


@app.route('/logout')
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route('/sync')
def sync():
    sync_full_dataset()
    return "Synced"


if __name__ == '__main__':
    app.run(debug=True)
