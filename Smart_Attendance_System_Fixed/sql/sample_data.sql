USE smart_attendance_db;

INSERT IGNORE INTO classes (class_name, section, academic_year)
VALUES ('B.Tech CSE', 'A', '2026-2027');

INSERT IGNORE INTO teachers (employee_id, teacher_name, email, phone, department)
VALUES ('T001', 'Demo Teacher', 'teacher@example.com', NULL, 'Computer Science');

INSERT IGNORE INTO subjects (subject_code, subject_name, class_id, teacher_id)
SELECT 'CS101', 'Python Programming', c.class_id, t.teacher_id
FROM classes c CROSS JOIN teachers t
WHERE c.class_name='B.Tech CSE' AND c.section='A'
  AND c.academic_year='2026-2027' AND t.employee_id='T001';

-- Optional demo account row for the "Marked by" dropdown.
-- This starter project does not implement login/authentication.
INSERT IGNORE INTO users (username, password_hash, role)
VALUES ('demo_teacher', 'NOT_A_LOGIN_PASSWORD', 'Teacher');
