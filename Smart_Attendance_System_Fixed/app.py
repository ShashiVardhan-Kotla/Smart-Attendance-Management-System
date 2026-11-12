import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import date

st.set_page_config(page_title="Smart Attendance System", page_icon="📋", layout="wide")

def get_db_config():
    defaults = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "Kotla@8886",
        "database": "smart_attendance_db",
    }
    try:
        secrets = st.secrets.get("mysql", {})
        for key in defaults:
            if key in secrets:
                defaults[key] = secrets[key]
    except Exception:
        pass
    return defaults

with st.sidebar:
    st.header("MySQL connection")
    cfg = get_db_config()
    host = st.text_input("Host", value=str(cfg["host"]))
    port = st.number_input("Port", min_value=1, max_value=65535, value=int(cfg["port"]))
    user = st.text_input("Username", value=str(cfg["user"]))
    password = st.text_input("Password", value=str(cfg["password"]), type="password")
    database = st.text_input("Database", value=str(cfg["database"]))
    connect_clicked = st.button("Connect to MySQL", use_container_width=True)

if "db_config" not in st.session_state or connect_clicked:
    st.session_state.db_config = {
        "host": host, "port": int(port), "user": user,
        "password": password, "database": database
    }

def connect():
    return mysql.connector.connect(**st.session_state.db_config)

def query_df(sql, params=None):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        columns = [item[0] for item in cur.description] if cur.description else []
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()

def execute(sql, params=None, many=False):
    conn = connect()
    try:
        cur = conn.cursor()
        if many:
            cur.executemany(sql, params)
        else:
            cur.execute(sql, params or ())
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()

try:
    test_conn = connect()
    test_conn.close()
except Error as e:
    st.error("Could not connect to MySQL.")
    st.code(str(e))
    st.info(
        "Check that MySQL Server is running, create the database by executing "
        "sql/schema.sql in MySQL Workbench, and verify the connection details in the sidebar."
    )
    st.stop()

st.title("📋 Smart Attendance Management System")
st.caption("Python + Streamlit + MySQL")

def show_error(fn):
    try:
        fn()
    except Error as e:
        st.error(f"MySQL error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")

pages = [
    "Dashboard", "Students", "Teachers", "Classes & Subjects",
    "Mark Attendance", "Attendance Reports"
]
page = st.sidebar.radio("Navigation", pages)

if page == "Dashboard":
    st.subheader("Dashboard overview")
    c1, c2, c3, c4 = st.columns(4)
    students_count = query_df("SELECT COUNT(*) AS n FROM students")["n"].iloc[0]
    teachers_count = query_df("SELECT COUNT(*) AS n FROM teachers")["n"].iloc[0]
    subjects_count = query_df("SELECT COUNT(*) AS n FROM subjects")["n"].iloc[0]
    records_count = query_df("SELECT COUNT(*) AS n FROM attendance")["n"].iloc[0]
    c1.metric("Students", int(students_count))
    c2.metric("Teachers", int(teachers_count))
    c3.metric("Subjects", int(subjects_count))
    c4.metric("Attendance records", int(records_count))

    st.markdown("### Recent attendance")
    recent = query_df("""
        SELECT a.attendance_date, s.roll_number, s.student_name,
               sub.subject_name, a.attendance_status
        FROM attendance a
        JOIN students s ON s.student_id = a.student_id
        JOIN subjects sub ON sub.subject_id = a.subject_id
        ORDER BY a.attendance_date DESC, a.attendance_id DESC
        LIMIT 15
    """)
    st.dataframe(recent, use_container_width=True, hide_index=True)

elif page == "Students":
    st.subheader("Student management")
    tab1, tab2, tab3 = st.tabs(["Add student", "View students", "Update / deactivate"])
    with tab1:
        classes = query_df("""
            SELECT class_id,
                   CONCAT(class_name, ' - ', section, ' (', academic_year, ')') AS label
            FROM classes ORDER BY class_id
        """)
        if classes.empty:
            st.warning("Add a class first in Classes & Subjects.")
        else:
            with st.form("add_student"):
                roll = st.text_input("Roll number")
                name = st.text_input("Student name")
                email = st.text_input("Email (optional)")
                phone = st.text_input("Phone (optional)")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                class_label = st.selectbox("Class", classes["label"].tolist())
                admission = st.date_input("Admission date", value=date.today())
                submitted = st.form_submit_button("Add student")
                if submitted:
                    if not roll.strip() or not name.strip():
                        st.error("Roll number and student name are required.")
                    else:
                        class_id = int(classes.loc[classes.label == class_label, "class_id"].iloc[0])
                        execute("""
                            INSERT INTO students
                            (roll_number, student_name, email, phone, gender, class_id, admission_date)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """, (roll.strip(), name.strip(), email.strip() or None,
                              phone.strip() or None, gender, class_id, admission))
                        st.success("Student added successfully.")
    with tab2:
        df = query_df("""
            SELECT s.student_id, s.roll_number, s.student_name, s.email, s.phone,
                   s.gender, c.class_name, c.section, s.student_status
            FROM students s JOIN classes c ON c.class_id=s.class_id
            ORDER BY s.student_id
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download students CSV", df.to_csv(index=False).encode("utf-8"),
                           "students.csv", "text/csv")
    with tab3:
        active = query_df("""
            SELECT student_id, roll_number, student_name, student_status
            FROM students ORDER BY student_id
        """)
        if not active.empty:
            chosen = st.selectbox(
                "Select student", active.itertuples(index=False),
                format_func=lambda x: f"{x.roll_number} - {x.student_name} ({x.student_status})"
            )
            new_status = st.selectbox("New status", ["Active", "Inactive"])
            if st.button("Update student status"):
                execute("UPDATE students SET student_status=%s WHERE student_id=%s",
                        (new_status, int(chosen.student_id)))
                st.success("Student status updated.")

elif page == "Teachers":
    st.subheader("Teacher management")
    with st.form("add_teacher"):
        emp = st.text_input("Employee ID")
        name = st.text_input("Teacher name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        dept = st.text_input("Department")
        if st.form_submit_button("Add teacher"):
            if not emp.strip() or not name.strip():
                st.error("Employee ID and teacher name are required.")
            else:
                execute("""
                    INSERT INTO teachers (employee_id, teacher_name, email, phone, department)
                    VALUES (%s,%s,%s,%s,%s)
                """, (emp.strip(), name.strip(), email.strip() or None,
                      phone.strip() or None, dept.strip() or None))
                st.success("Teacher added successfully.")
    df = query_df("SELECT * FROM teachers ORDER BY teacher_id")
    st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Classes & Subjects":
    st.subheader("Classes and subjects")
    tab1, tab2 = st.tabs(["Add class", "Add subject / view"])
    with tab1:
        with st.form("add_class"):
            class_name = st.text_input("Class name", placeholder="B.Tech CSE")
            section = st.text_input("Section", value="A")
            year = st.text_input("Academic year", value="2026-2027")
            if st.form_submit_button("Add class"):
                if not class_name.strip() or not section.strip() or not year.strip():
                    st.error("Class name, section and academic year are required.")
                else:
                    execute("""
                        INSERT INTO classes (class_name, section, academic_year)
                        VALUES (%s,%s,%s)
                    """, (class_name.strip(), section.strip(), year.strip()))
                    st.success("Class added.")
    with tab2:
        teachers = query_df("SELECT teacher_id, teacher_name FROM teachers ORDER BY teacher_name")
        classes = query_df("""
            SELECT class_id, CONCAT(class_name,' - ',section) AS label
            FROM classes ORDER BY class_id
        """)
        if teachers.empty or classes.empty:
            st.info("Add at least one teacher and one class before adding subjects.")
        else:
            with st.form("add_subject"):
                code = st.text_input("Subject code")
                subject = st.text_input("Subject name")
                clabel = st.selectbox("Class", classes.label.tolist())
                tlabel = st.selectbox("Teacher", teachers.teacher_name.tolist())
                if st.form_submit_button("Add subject"):
                    if not code.strip() or not subject.strip():
                        st.error("Subject code and subject name are required.")
                    else:
                        cid = int(classes.loc[classes.label == clabel, "class_id"].iloc[0])
                        tid = int(teachers.loc[teachers.teacher_name == tlabel, "teacher_id"].iloc[0])
                        execute("""
                            INSERT INTO subjects (subject_code, subject_name, class_id, teacher_id)
                            VALUES (%s,%s,%s,%s)
                        """, (code.strip(), subject.strip(), cid, tid))
                        st.success("Subject added.")
        st.markdown("#### Existing classes")
        st.dataframe(query_df("SELECT * FROM classes ORDER BY class_id"),
                     use_container_width=True, hide_index=True)
        st.markdown("#### Existing subjects")
        st.dataframe(query_df("""
            SELECT sub.subject_id, sub.subject_code, sub.subject_name,
                   c.class_name, c.section, t.teacher_name
            FROM subjects sub
            JOIN classes c ON c.class_id=sub.class_id
            JOIN teachers t ON t.teacher_id=sub.teacher_id
            ORDER BY sub.subject_id
        """), use_container_width=True, hide_index=True)

elif page == "Mark Attendance":
    st.subheader("Mark daily attendance")
    classes = query_df("""
        SELECT class_id, CONCAT(class_name, ' - ', section) AS label
        FROM classes ORDER BY class_id
    """)
    if classes.empty:
        st.warning("Create a class first.")
    else:
        clabel = st.selectbox("Select class", classes.label.tolist())
        cid = int(classes.loc[classes.label == clabel, "class_id"].iloc[0])
        subjects = query_df("""
            SELECT subject_id, subject_name FROM subjects
            WHERE class_id=%s ORDER BY subject_name
        """, (cid,))
        students = query_df("""
            SELECT student_id, roll_number, student_name
            FROM students WHERE class_id=%s AND student_status='Active'
            ORDER BY roll_number
        """, (cid,))
        if subjects.empty:
            st.warning("No subjects are assigned to this class.")
        elif students.empty:
            st.warning("No active students are registered in this class.")
        else:
            sub_name = st.selectbox("Subject", subjects.subject_name.tolist())
            sid = int(subjects.loc[subjects.subject_name == sub_name, "subject_id"].iloc[0])
            att_date = st.date_input("Attendance date", value=date.today())
            teacher_users = query_df("""
                SELECT user_id, username FROM users
                WHERE role IN ('Admin','Teacher') ORDER BY username
            """)
            marker = None
            if not teacher_users.empty:
                marker_name = st.selectbox("Marked by", teacher_users.username.tolist())
                marker = int(teacher_users.loc[
                    teacher_users.username == marker_name, "user_id"
                ].iloc[0])
            else:
                st.warning("No Admin/Teacher user exists in users. Attendance can still be saved without a marker.")
            st.caption("Choose a status for each student, then save all records.")
            statuses = {}
            for row in students.itertuples(index=False):
                statuses[int(row.student_id)] = st.selectbox(
                    f"{row.roll_number} — {row.student_name}",
                    ["Present", "Absent", "Late", "Excused"],
                    key=f"att_{row.student_id}_{sid}_{att_date}"
                )
            if st.button("Save attendance", type="primary"):
                conn = connect()
                try:
                    cur = conn.cursor()
                    for student_id, status in statuses.items():
                        cur.execute("""
                            INSERT INTO attendance
                            (student_id, subject_id, attendance_date, attendance_status, marked_by)
                            VALUES (%s,%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE
                            attendance_status=VALUES(attendance_status),
                            marked_by=VALUES(marked_by)
                        """, (student_id, sid, att_date, status, marker))
                    conn.commit()
                    st.success(f"Attendance saved for {len(statuses)} students.")
                finally:
                    conn.close()

elif page == "Attendance Reports":
    st.subheader("Attendance reports")
    students = query_df("""
        SELECT student_id, roll_number, student_name FROM students ORDER BY roll_number
    """)
    if students.empty:
        st.info("No students found. Add students first.")
    else:
        report_type = st.radio(
            "Report type",
            ["Overall student report", "Date-wise report", "Monthly report"],
            horizontal=True
        )
        if report_type == "Overall student report":
            df = query_df("""
                SELECT s.roll_number, s.student_name, c.class_name, c.section,
                       COUNT(a.attendance_id) AS total_classes,
                       COALESCE(SUM(a.attendance_status='Present'), 0) AS present_days,
                       COALESCE(SUM(a.attendance_status='Absent'), 0) AS absent_days,
                       COALESCE(SUM(a.attendance_status='Late'), 0) AS late_days,
                       ROUND(100.0 * COALESCE(SUM(a.attendance_status IN ('Present','Late')),0)
                             / NULLIF(COUNT(a.attendance_id),0), 2) AS attendance_percentage
                FROM students s
                JOIN classes c ON c.class_id=s.class_id
                LEFT JOIN attendance a ON a.student_id=s.student_id
                GROUP BY s.student_id, s.roll_number, s.student_name, c.class_name, c.section
                ORDER BY s.roll_number
            """)
        elif report_type == "Date-wise report":
            chosen_date = st.date_input("Choose date", value=date.today(), key="date_report")
            df = query_df("""
                SELECT a.attendance_date, s.roll_number, s.student_name,
                       sub.subject_name, a.attendance_status
                FROM attendance a
                JOIN students s ON s.student_id=a.student_id
                JOIN subjects sub ON sub.subject_id=a.subject_id
                WHERE a.attendance_date=%s
                ORDER BY sub.subject_name, s.roll_number
            """, (chosen_date,))
        else:
            col1, col2 = st.columns(2)
            year = col1.number_input("Year", min_value=2000, max_value=2100, value=date.today().year)
            month = col2.selectbox("Month", list(range(1, 13)), index=date.today().month - 1)
            df = query_df("""
                SELECT s.roll_number, s.student_name, sub.subject_name,
                       COUNT(*) AS total_classes,
                       SUM(a.attendance_status='Present') AS present,
                       SUM(a.attendance_status='Absent') AS absent,
                       ROUND(100.0 * SUM(a.attendance_status IN ('Present','Late'))
                             / NULLIF(COUNT(*),0), 2) AS attendance_percentage
                FROM attendance a
                JOIN students s ON s.student_id=a.student_id
                JOIN subjects sub ON sub.subject_id=a.subject_id
                WHERE YEAR(a.attendance_date)=%s AND MONTH(a.attendance_date)=%s
                GROUP BY s.student_id, s.roll_number, s.student_name,
                         sub.subject_id, sub.subject_name
                ORDER BY s.roll_number, sub.subject_name
            """, (int(year), int(month)))
        st.dataframe(df, use_container_width=True, hide_index=True)
        if "attendance_percentage" in df.columns:
            low = df[df.attendance_percentage.fillna(0) < 75]
            st.markdown("### Students below 75% attendance")
            st.dataframe(low, use_container_width=True, hide_index=True)
        st.download_button(
            "Download report as CSV", df.to_csv(index=False).encode("utf-8"),
            "attendance_report.csv", "text/csv"
        )

st.sidebar.divider()
st.sidebar.caption("Smart Attendance Management System")
