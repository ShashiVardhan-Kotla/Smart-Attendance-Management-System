CREATE DATABASE IF NOT EXISTS smart_attendance_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_attendance_db;

CREATE TABLE IF NOT EXISTS classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    section VARCHAR(20) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    UNIQUE KEY uq_class_section_year (class_name, section, academic_year)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    teacher_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NULL,
    phone VARCHAR(30) NULL,
    department VARCHAR(100) NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_number VARCHAR(50) NOT NULL UNIQUE,
    student_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NULL,
    phone VARCHAR(30) NULL,
    gender ENUM('Male','Female','Other') NOT NULL DEFAULT 'Other',
    class_id INT NOT NULL,
    admission_date DATE NOT NULL,
    student_status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    CONSTRAINT fk_students_class FOREIGN KEY (class_id)
        REFERENCES classes(class_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(50) NOT NULL UNIQUE,
    subject_name VARCHAR(150) NOT NULL,
    class_id INT NOT NULL,
    teacher_id INT NOT NULL,
    CONSTRAINT fk_subjects_class FOREIGN KEY (class_id)
        REFERENCES classes(class_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_subjects_teacher FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Admin','Teacher') NOT NULL DEFAULT 'Teacher'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    attendance_status ENUM('Present','Absent','Late','Excused') NOT NULL,
    marked_by INT NULL,
    CONSTRAINT uq_student_subject_date UNIQUE (student_id, subject_id, attendance_date),
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_subject FOREIGN KEY (subject_id)
        REFERENCES subjects(subject_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_user FOREIGN KEY (marked_by)
        REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE OR REPLACE VIEW vw_student_attendance_summary AS
SELECT s.student_id, s.roll_number, s.student_name,
       COUNT(a.attendance_id) AS total_classes,
       COALESCE(SUM(a.attendance_status IN ('Present','Late')),0) AS attended_classes,
       ROUND(100.0 * COALESCE(SUM(a.attendance_status IN ('Present','Late')),0)
             / NULLIF(COUNT(a.attendance_id),0), 2) AS attendance_percentage
FROM students s
LEFT JOIN attendance a ON a.student_id=s.student_id
GROUP BY s.student_id, s.roll_number, s.student_name;
