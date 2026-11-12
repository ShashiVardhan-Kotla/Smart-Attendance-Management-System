# Smart Attendance Management System

A Python + Streamlit + MySQL college project.

## Features
- Dashboard counts and recent attendance
- Add, view, and deactivate students
- Add and view teachers
- Manage classes and subjects
- Mark daily attendance by class, subject, and date
- Prevent duplicate attendance for the same student/subject/date
- Overall, date-wise, and monthly reports
- Attendance percentage and below-75% report
- CSV downloads

## Requirements
- Python 3.10 or newer (Python 3.13 is supported by the listed dependencies)
- MySQL Server 8.0.16 or newer
- MySQL Workbench (recommended)

## Setup on Windows

1. Extract this folder and open it in VS Code.
2. Start your MySQL Server.
3. In MySQL Workbench, connect to your local server.
4. Open `sql/schema.sql` and execute the whole script (lightning icon). This creates `smart_attendance_db` and all required tables.
5. Optional: execute `sql/sample_data.sql` to add a demo class, teacher, subject and a dropdown user.
6. Open the VS Code terminal in this project folder and run:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks virtual-environment activation, run this instead without activation:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit should open `http://localhost:8501` in your browser. **Do not start this app with `python app.py`; use `streamlit run app.py`.**

## MySQL connection
Enter your MySQL host, port, username, password and database in the app's left sidebar. The default database name is `smart_attendance_db`. The password field is intentionally blank; enter your own MySQL password.

Alternatively, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and edit it with your own credentials. Never share the real `secrets.toml` or commit it to source control.

## Troubleshooting
- `Unknown database 'smart_attendance_db'`: execute `sql/schema.sql` in MySQL Workbench and check that the database name in the sidebar is exactly `smart_attendance_db`.
- `Access denied for user`: verify your MySQL username and password in the sidebar.
- `Can't connect to MySQL server`: start the MySQL Server Windows service and verify host `localhost` and port `3306`.
- `No module named ...`: install dependencies using `pip install -r requirements.txt` with the same Python environment used to run Streamlit.

## Database tables
`classes`, `teachers`, `students`, `subjects`, `users`, and `attendance`.

## Important notes
- The starter app does not implement authentication even though the `users` table supports the attendance marker dropdown.
- The optional demo user is not a login account.
- For real deployment, add authentication and role-based authorization, validate all relationships server-side, use a least-privilege MySQL account rather than `root`, and configure database backups.
- The report counts `Present` and `Late` as attended. `Absent` and `Excused` are not counted as attended.
