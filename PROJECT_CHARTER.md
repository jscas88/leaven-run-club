# Leaven Run Club Tracker (LRCT)

## 1. Project Name
Leaven Run Club Tracker (LRCT)

## 2. Project Purpose
Leaven Run Club needs a simple, reliable system to:

- Track weekly attendance
- Maintain runner profiles with privacy controls
- Capture liability waivers
- Sync data to Google Sheets
- Generate weekly digests and streak summaries
- Provide an admin-only interface with PIN lock

The goal is to replace manual check-ins and scattered spreadsheets with a unified, branded, secure tool.

## 3. Project Objectives
Build a mobile-friendly Flask web app for check-ins

- Store runner data and attendance in SQLite (or PostgreSQL later)
- Enforce privacy masking for phone numbers and referral sources
- Integrate Google Sheets sync for warehouse-style data storage
- Add emoji avatars and branded UI
- Automate weekly email digests
- Provide admin controls (PIN lock, edit runners, export data)
- Maintain a waiver system with timestamped acceptance

## 4. Scope
### In Scope
- Runner registration
- Attendance check-in
- Waiver capture + storage
- Admin dashboard
- Google Sheets sync
- Weekly digest automation
- Streak tracking
- Branded UI (green/yellow + hop cone mascot)
- Privacy masking

### Out of Scope (for now)
- Payment processing
- GPS run tracking
- Social features
- Mobile app (native)

## 5. Deliverables
Flask application with:

- `/` Today’s check-ins
- `/runners` Runner list + add form
- `/checkin/<id>` Quick check-in
- `/admin` PIN-protected dashboard
- `/waiver` Digital waiver flow

SQLite database with:

- Runner table
- Attendance table
- Waiver table

Additional components:

- Google Sheets integration script
- Weekly digest email script
- Branded UI with avatars
