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
    if not rows:
        return []

    headers = rows[0]
    data = rows[1:]

    runners = []
    for row in data:
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

        runners.append({
            "id": int(row[0]),
            "name": row[1],
            "phone": row[2],
            "referral": row[3],
            "avatar": row[4],
            "shoe": row[5],
            "waiver_signed": row[6]
        })
    return runners


def get_attendance():
    rows = get_all_rows(ATTENDANCE_WS)
    if not rows:
        return []

    headers = rows[0]
    data = rows[1:]

    attendance = []
    for row in data:
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

        attendance.append({
            "id": int(row[0]),
            "date": row[1],
            "verified": row[2],
            "reward_date": row[3] if len(row) > 3 else ""
        })
    return attendance


def add_attendance(runner_id):
    today = date.today().strftime("%Y-%m-%d")
    append_row(ATTENDANCE_WS, [runner_id, today, "No"])


# -----------------------------
# Detect duplicates
# -----------------------------
def find_duplicate_runners():
    runners = get_runners()
    id_map = {}

    for r in runners:
        if r["name"] not in id_map:
            id_map[r["name"]] = []
        id_map[r["name"]].append(r)

    duplicates = {name: items for name, items in id_map.items() if len(items) > 1}
    return duplicates


# -----------------------------
# WEEKLY ATTENDANCE (SAFE)
# -----------------------------
def get_weekly_attendance():
    attendance = get_attendance()
    if not attendance:
        return {}

    parsed = []
    for a in attendance:
        try:
            d = datetime.strptime(a["date"], "%Y-%m-%d").date()
            parsed.append({"id": a["id"], "date": d, "verified": a["verified"]})
        except:
            continue

    weekly = {}
    for a in parsed:
        week_start = a["date"] - timedelta(days=a["date"].weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in weekly:
            weekly[week_key] = {
                "week_start": week_start,
                "runs": 0,
                "verified_runs": 0,
                "pending_runs": 0,
                "runners": set()
            }

        weekly[week_key]["runs"] += 1
        weekly[week_key]["runners"].add(a["id"])

        if a["verified"].lower() == "yes":
            weekly[week_key]["verified_runs"] += 1
        else:
            weekly[week_key]["pending_runs"] += 1

    return weekly


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
    checked_in_today = {a["id"] for a in attendance if a["date"] == today}

    for r in runners:
        r["checked_in_today"] = r["id"] in checked_in_today

    return render_template("checking.html", runners=runners)


# -----------------------------
# CHECK-IN ENDPOINT
# -----------------------------
@app.route("/checkin_runner/<int:runner_id>", methods=["POST"])
def checkin_runner(runner_id):
    add_attendance(runner_id)
    return redirect(url_for("rewards"))


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
# ADMIN VERIFY PAGE (ID-BASED)
# -----------------------------
@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if not is_admin():
        return redirect(url_for("admin_login"))

    sheet = get_sheet(ATTENDANCE_WS)
    rows = sheet.get_all_values()
    today = date.today().strftime("%Y-%m-%d")

    pending = []
    for idx, row in enumerate(rows[1:], start=2):
        runner_id, row_date, verified = row[0], row[1], row[2]
        if row_date == today and verified != "Yes":
            pending.append({
                "row_index": idx,
                "id": int(runner_id),
                "date": row_date
            })

    duplicates = find_duplicate_runners()

    if request.method == "POST":
        row_index = int(request.form.get("row_index"))

        sheet.update_cell(row_index, 3, "Yes")

        attendance = get_attendance()
        runner_id = int(rows[row_index - 1][0])

        total_runs = sum(
            1 for a in attendance
            if a["id"] == runner_id and a["verified"] == "Yes"
        )

        earned, next_reward = get_runner_rewards(total_runs)

        if earned:
            last_reward = earned[-1]
            sheet.update_cell(row_index, 4, f"{last_reward} earned on {today}")

        return redirect(url_for("admin_verify"))

    return render_template("admin_verify.html", pending=pending, duplicates=duplicates)


# -----------------------------
# ADMIN CLEAR ALL PENDING
# -----------------------------
@app.route("/admin/clear_pending", methods=["POST"])
def clear_pending():
    if not is_admin():
        return redirect(url_for("admin_login"))

    sheet = get_sheet(ATTENDANCE_WS)
    rows = sheet.get_all_values()

    if not rows or len(rows) == 1:
        return redirect(url_for("admin_verify"))

    today = date.today().strftime("%Y-%m-%d")

    new_rows = [rows[0]]

    for row in rows[1:]:
        runner_id, row_date, verified = row[0], row[1], row[2]
        if row_date != today or verified == "Yes":
            new_rows.append(row)

    sheet.clear()
    sheet.update("A1", new_rows)

    return redirect(url_for("admin_verify"))


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_admin():
        return redirect(url_for("admin_login"))

    weekly = get_weekly_attendance()

    runners = get_runners()
    attendance = get_attendance()

    for r in runners:
        total_runs = sum(
            1 for a in attendance
            if a["id"] == r["id"] and a["verified"] == "Yes"
        )
        r["total_runs"] = total_runs

        earned, next_reward = get_runner_rewards(total_runs)
        r["earned_rewards"] = earned
        r["next_reward"] = next_reward

    sorted_weeks = dict(sorted(
        weekly.items(),
        key=lambda x: x[1]["week_start"],
        reverse=True
    ))

    return render_template("admin_dashboard.html", weekly=sorted_weeks, runners=runners)


# -----------------------------
# DELETE RUNNERS
# -----------------------------
@app.route("/admin/delete_runners", methods=["POST"])
def delete_runners():
    if not is_admin():
        return redirect(url_for("admin_login"))

    to_delete = request.form.getlist("delete_ids")

    sheet = get_sheet(RUNNERS_WS)
    rows = sheet.get_all_values()

    new_rows = [rows[0]]

    for idx, row in enumerate(rows[1:], start=2):
        row_id = str(idx)
        if row_id not in to_delete:
            new_rows.append(row)

    sheet.clear()
    sheet.update("A1", new_rows)

    return redirect(url_for("admin_verify"))


# -----------------------------
# Reward Tier Table
# -----------------------------
REWARD_TIERS = [
    (2, "🍺 Beer"),
    (4, "🍺 Beer"),
    (10, "👕 T-Shirt"),
    (11, "🍺 Beer"),
    (13, "🍺 Beer"),
    (15, "📎 Stickers"),
    (18, "🍺 Beer Flight"),
    (20, "🍺 Beer"),
    (23, "🍺 Beer"),
    (24, "🧲 Magnet"),
    (26, "🥨 Nachos")
]


# -----------------------------
# Streak Calculator
# -----------------------------
def calculate_streak(runner_id, attendance):
    dates = sorted([
        datetime.strptime(a["date"], "%Y-%m-%d")
        for a in attendance
        if a["id"] == runner_id and a["verified"] == "Yes"
    ])

    if not dates:
        return 0

    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


# -----------------------------
# Reward Engine
# -----------------------------
def get_runner_rewards(total_runs):
    earned = []
    next_reward = None

    for runs_required, reward_name in REWARD_TIERS:
        if total_runs >= runs_required:
            earned.append(reward_name)
        elif next_reward is None:
            next_reward = {
                "runs_required": runs_required,
                "name": reward_name,
                "remaining": runs_required - total_runs,
                "progress": int((total_runs / runs_required) * 100)
            }

    if next_reward is None:
        next_reward = {
            "runs_required": None,
            "name": "All rewards earned!",
            "remaining": 0,
            "progress": 100
        }

    return earned, next_reward


# -----------------------------
# ADD RUNNER PAGE
# -----------------------------
@app.route("/runners", methods=["GET", "POST"])
def runners_page():
    form = AddRunnerForm()
    runners = get_runners()

    if form.validate_on_submit():
        rows = get_all_rows(RUNNERS_WS)
        new_id = len(rows)

        append_row(RUNNERS_WS, [
            new_id,
            form.name.data,
            form.phone.data,
            form.referral.data,
            form.avatar.data,
            form.shoe.data,
            form.waiver_signed.data
        ])

        session["new_runner_added"] = True
        return redirect(url_for("checking"))

    return render_template("runners.html", form=form, runners=runners)


# -----------------------------
# REWARDS PAGE
# -----------------------------
@app.route("/rewards")
def rewards():
    runners = get_runners()
    attendance = get_attendance()

    for r in runners:
        total_runs = sum(
            1 for a in attendance
            if a["id"] == r["id"] and a["verified"] == "Yes"
        )
        r["total_runs"] = total_runs

        r["streak"] = calculate_streak(r["id"], attendance)

        earned, next_reward = get_runner_rewards(total_runs)
        r["earned_rewards"] = earned
        r["next_reward"] = next_reward

    return render_template("rewards.html", runners=runners)


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
