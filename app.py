@app.route('/rewards')
def rewards():
    all_runners = Runner.query.all()
    today = date.today()

    # -----------------------------
    # Monthly Leaderboard
    # -----------------------------
    first_of_month = today.replace(day=1)
    monthly_attendance = Attendance.query.filter(Attendance.date >= first_of_month).all()

    # Count runs per runner this month
    monthly_counts = {}
    for a in monthly_attendance:
        monthly_counts[a.runner_id] = monthly_counts.get(a.runner_id, 0) + 1

    # Most runs this month
    if monthly_counts:
        top_runner_id = max(monthly_counts, key=monthly_counts.get)
        top_runner = Runner.query.get(top_runner_id)
        top_runner_name = top_runner.name
        top_runner_count = monthly_counts[top_runner_id]
    else:
        top_runner_name = None
        top_runner_count = 0

    # -----------------------------
    # Build runner reward data
    # -----------------------------
    runners_data = []
    all_attendance = Attendance.query.all()

    # Build attendance history for heatmap
    attendance_by_date = {}
    for a in all_attendance:
        attendance_by_date[a.date] = attendance_by_date.get(a.date, 0) + 1

    # Auto-scale heatmap range
    if attendance_by_date:
        min_date = min(attendance_by_date.keys())
        max_date = max(attendance_by_date.keys())
    else:
        min_date = today
        max_date = today

    # Build timeline list
    timeline = []
    current = min_date
    while current <= max_date:
        timeline.append({
            "date": current,
            "count": attendance_by_date.get(current, 0)
        })
        current += timedelta(days=1)

    # Runner-specific data
    for r in all_runners:
        dates = [a.date for a in Attendance.query.filter_by(runner_id=r.id).all()]
        streak = calculate_streak(dates)
        total_runs = len(dates)

        # Milestones
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
