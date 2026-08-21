from flask import Flask, render_template, redirect, jsonify, session, url_for, request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from google_sheets import get_sheet, append_row, get_all_rows
from forms import AddRunnerForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'


# -----------------------------
# ADMIN PIN SYSTEM
# -----------------------------
ADMIN_PIN = "0710"

def is_admin():
    return session.get("admin_logged_in", False)


# -----------------------------
# NEXT RUN CALCULATION (Friday 6:30 PM)
# -----------------------------
def get_next_run():
    now = datetime.now(ZoneInfo("America/New_York"))
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

    start_of_week = start_date - timedelta(days=start_date.weekday() + 1 if start_date.weekday() < 6 else 0)
    days = [start_of_week + timedelta(days=i) for i in range(28)]
    weeks = [days[i:i+7] for i in range(0, 28, 7)]
    return weeks


# -----------------------------
# GOOGLE SHEETS HELPERS
# -----------------------------
RUNNERS_WS = "Runners"
ATTENDANCE_WS = "Attendance"

def get_runners():
    rows = get_all_rows(RUNNERS_WS)
    headers = rows[0]
    data = rows[1:]

    runners = []
    for row in data:
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

        runners.append({
            "name": row[0],
            "phone": row[1],
            "referral": row[2],
            "emoji": row[3],
            "shoe_brand": row[4],
            "waiver_signed": row[5]
        })
    return runners


def get_attendance():
    rows = get_all_rows(ATTENDANCE_WS)
    headers = rows[0]
    data = rows[1:]

    attendance = []
    for row in data:
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

        attendance.append({
            "name": row[0],
            "date": row[1],
            "verified": row[2]
        })
    return attendance


def add_attendance(name):
    today = date.today().strftime("%Y-%m-%d")
    append_row(ATTENDANCE_WS, [name, today, "No"])   # <-- unverified until admin approves


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def index():
    next_run = get_next_run()
    weeks = get_four_week_calendar()
    fridays = [d for week in weeks for d in week if d.weekday() == 4]
    next_run_ts = int(next_run.timestamp() * 1000)

    return render_template(
        "index.html",
        next_run=next_run,
        next_run_ts=next_run_ts,
        weeks=weeks,
        fridays=fridays,
        date=date
    )


# -----------------------------
# CHECK-IN PAGE
# -----------------------------
@app.route("/checking", methods=["GET"])
def checking():
    runners = get_runners()
    attendance = get_attendance()

    today = date.today().strftime("%Y-%m-%d")
    checked_in_today = {a["name"] for a in attendance if a["date"] == today}

    for r in runners:
        r["checked_in_today"] = r["name"] in checked_in_today

    return render_template("checking.html", runners=runners)


# -----------------------------
# CHECK-IN ENDPOINT
# -----------------------------
@app.route("/checkin_runner/<string:runner_name>", methods=["POST"])
def checkin_runner(runner_name):
    add_attendance(runner_name)
    return redirect(url_for("checking"))


# -----------------------------
# ADMIN LOGIN
# -----------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pin = request.form.get("pin")
        if pin == ADMIN_PIN:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_verify"))
        else:
            return render_template("admin_login.html", error="Incorrect PIN")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# -----------------------------
# ADMIN VERIFY PAGE
# -----------------------------
@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if not is_admin():
        return redirect(url_for("admin_login"))

    attendance = get_attendance()
    today = date.today().strftime("%Y-%m-%d")

    # Only today's unverified check-ins
    pending = [a for a in attendance if a["date"] == today and a["verified"] != "Yes"]

    if request.method == "POST":
        name = request.form.get("runner_name")

        sheet = get_sheet(ATTENDANCE_WS)
        rows = sheet.get_all_values()

        for idx, row in enumerate(rows):
            if idx == 0:
                continue
            if row[0] == name and row[1] == today:
                sheet.update_cell(idx + 1, 3, "Yes")   # <-- mark verified
                break

        return redirect(url_for("admin_verify"))

    return render_template("admin_verify.html", pending=pending)


# -----------------------------
# ADD RUNNER PAGE
# -----------------------------
@app.route("/runners", methods=["GET", "POST"])
def runners_page():
    form = AddRunnerForm()
    runners = get_runners()

    if form.validate_on_submit():
        append_row(RUNNERS_WS, [
            form.name.data,
            form.phone.data,
            form.referral.data,
            form.emoji.data,
            form.shoe_brand.data,
            form.waiver_signed.data
        ])

        session["new_runner_added"] = True
        return redirect(url_for("checking"))

    return render_template("runners.html", form=form, runners=runners)


# -----------------------------
# REWARDS PAGE (verified only)
# -----------------------------
@app.route("/rewards")
def rewards():
    runners = get_runners()
    attendance = get_attendance()

    verified_attendance = [
        a for a in attendance
        if str(a["verified"]).strip().lower() == "yes"
    ]

    return render_template("rewards.html", runners=runners, attendance=verified_attendance)


# -----------------------------
# CLEAR TOAST FLAG
# -----------------------------
@app.route("/clear_new_runner_flag", methods=["POST"])
def clear_new_runner_flag():
    session.pop("new_runner_added", None)
    return jsonify({"cleared": True})


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
