-- VORTEXA 3.0 base schema for local MySQL (database is selected by backend/.env).
-- Safe to re-run: creates tables only if they do not already exist.

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('jobseeker', 'employer', 'admin') NOT NULL DEFAULT 'jobseeker',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS jobs (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    employer_id INT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    skills_required TEXT,
    location VARCHAR(150),
    salary_range VARCHAR(100),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_jobs_employer FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS applications (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id INT UNSIGNED NOT NULL,
    applicant_id INT UNSIGNED NOT NULL,
    status ENUM('pending', 'reviewed', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_application (job_id, applicant_id),
    CONSTRAINT fk_applications_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    CONSTRAINT fk_applications_applicant FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Candidate profile and skill-assessment extension. Additive and safe to rerun.
CREATE TABLE IF NOT EXISTS candidate_profiles (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  phone VARCHAR(25) NULL,
  experience VARCHAR(150) NULL,
  bio TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_education (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  degree VARCHAR(100) NULL,
  branch VARCHAR(120) NULL,
  college VARCHAR(200) NULL,
  graduation_year SMALLINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_education_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skills (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_skills (
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, skill_id),
  CONSTRAINT fk_candidate_skills_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_candidate_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_questions (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  skill_id INT UNSIGNED NOT NULL,
  question_text TEXT NOT NULL,
  option_a VARCHAR(500) NOT NULL,
  option_b VARCHAR(500) NOT NULL,
  option_c VARCHAR(500) NOT NULL,
  option_d VARCHAR(500) NOT NULL,
  correct_option CHAR(1) NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL DEFAULT 10,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_questions_skill_active (skill_id, active),
  CONSTRAINT fk_question_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  status ENUM('IN_PROGRESS','COMPLETED','TERMINATED') NOT NULL DEFAULT 'IN_PROGRESS',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  time_limit_seconds INT NOT NULL DEFAULT 900,
  score INT NOT NULL DEFAULT 0,
  total_marks INT NOT NULL DEFAULT 0,
  percentage DECIMAL(5,2) NULL,
  submitted_at DATETIME NULL,
  finish_reason VARCHAR(30) NULL,
  INDEX idx_attempt_user_skill (user_id, skill_id, status),
  CONSTRAINT fk_attempt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempt_questions (
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  question_number SMALLINT UNSIGNED NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (attempt_id, question_id),
  UNIQUE KEY uq_attempt_question_number (attempt_id, question_number),
  CONSTRAINT fk_attempt_question_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_question_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_answers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  selected_answer CHAR(1) NULL,
  is_correct TINYINT(1) NOT NULL DEFAULT 0,
  marks_awarded SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  UNIQUE KEY uq_attempt_answer (attempt_id, question_id),
  CONSTRAINT fk_answer_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_answer_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_results (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL UNIQUE,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  score INT NOT NULL,
  total_marks INT NOT NULL,
  percentage DECIMAL(5,2) NOT NULL,
  correct_count INT NOT NULL,
  status ENUM('COMPLETED','TERMINATED') NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_result_user (user_id),
  CONSTRAINT fk_result_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skill_passports (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  passport_code VARCHAR(40) NOT NULL UNIQUE,
  generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_passport_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO skills(name) VALUES
('Python'),('C++'),('C'),('Java'),('JavaScript'),('HTML'),('CSS'),('SQL'),('MySQL'),('Data Structures & Algorithms'),('Machine Learning'),('Data Analysis'),('Git & GitHub'),('Flask');

-- Starter question bank (answers are stored server-side and never sent to the browser).
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword defines a function in Python?','func','def','function','lambda','B',10 FROM skills s WHERE s.name='Python' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which type is immutable in Python?','list','dict','set','tuple','D',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'What does len([1,2,3]) return?','2','3','4','An error','B',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which is the correct way to declare an integer in C++?','integer x;','int x;','num x;','var x;','B',10 FROM skills s WHERE s.name='C++' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which operator accesses a member through an object pointer?','.','::','->','&','C',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which header provides std::vector?','<vector>','<array>','<list>','<map>','A',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which SQL clause filters rows before grouping?','ORDER BY','WHERE','HAVING','LIMIT','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which command reads rows from a table?','GET','READ','SELECT','OPEN','C',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which key uniquely identifies each row?','Foreign key','Primary key','Index only','View','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which HTML element creates a hyperlink?','<link>','<a>','<href>','<url>','B',10 FROM skills s WHERE s.name='HTML' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which attribute provides alternative text for an image?','title','src','alt','name','C',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which element is used for the main page heading?','<head>','<h1>','<header>','<title>','B',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword declares a block-scoped variable in JavaScript?','var only','let','dim','define','B',10 FROM skills s WHERE s.name='JavaScript' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which method converts JSON text into an object?','JSON.stringify','JSON.parse','JSON.object','JSON.read','B',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which array method adds an item to the end?','pop','shift','push','slice','C',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;


-- Candidate profile and skill-assessment extension. Additive and safe to rerun.
CREATE TABLE IF NOT EXISTS candidate_profiles (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  phone VARCHAR(25) NULL,
  experience VARCHAR(150) NULL,
  bio TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_education (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  degree VARCHAR(100) NULL,
  branch VARCHAR(120) NULL,
  college VARCHAR(200) NULL,
  graduation_year SMALLINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_education_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skills (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_skills (
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, skill_id),
  CONSTRAINT fk_candidate_skills_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_candidate_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_questions (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  skill_id INT UNSIGNED NOT NULL,
  question_text TEXT NOT NULL,
  option_a VARCHAR(500) NOT NULL,
  option_b VARCHAR(500) NOT NULL,
  option_c VARCHAR(500) NOT NULL,
  option_d VARCHAR(500) NOT NULL,
  correct_option CHAR(1) NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL DEFAULT 10,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_questions_skill_active (skill_id, active),
  CONSTRAINT fk_question_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  status ENUM('IN_PROGRESS','COMPLETED','TERMINATED') NOT NULL DEFAULT 'IN_PROGRESS',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  time_limit_seconds INT NOT NULL DEFAULT 900,
  score INT NOT NULL DEFAULT 0,
  total_marks INT NOT NULL DEFAULT 0,
  percentage DECIMAL(5,2) NULL,
  submitted_at DATETIME NULL,
  finish_reason VARCHAR(30) NULL,
  INDEX idx_attempt_user_skill (user_id, skill_id, status),
  CONSTRAINT fk_attempt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempt_questions (
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  question_number SMALLINT UNSIGNED NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (attempt_id, question_id),
  UNIQUE KEY uq_attempt_question_number (attempt_id, question_number),
  CONSTRAINT fk_attempt_question_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_question_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_answers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  selected_answer CHAR(1) NULL,
  is_correct TINYINT(1) NOT NULL DEFAULT 0,
  marks_awarded SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  UNIQUE KEY uq_attempt_answer (attempt_id, question_id),
  CONSTRAINT fk_answer_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_answer_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_results (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL UNIQUE,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  score INT NOT NULL,
  total_marks INT NOT NULL,
  percentage DECIMAL(5,2) NOT NULL,
  correct_count INT NOT NULL,
  status ENUM('COMPLETED','TERMINATED') NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_result_user (user_id),
  CONSTRAINT fk_result_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skill_passports (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  passport_code VARCHAR(40) NOT NULL UNIQUE,
  generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_passport_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO skills(name) VALUES
('Python'),('C++'),('C'),('Java'),('JavaScript'),('HTML'),('CSS'),('SQL'),('MySQL'),('Data Structures & Algorithms'),('Machine Learning'),('Data Analysis'),('Git & GitHub'),('Flask');

-- Starter question bank (answers are stored server-side and never sent to the browser).
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword defines a function in Python?','func','def','function','lambda','B',10 FROM skills s WHERE s.name='Python' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which type is immutable in Python?','list','dict','set','tuple','D',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'What does len([1,2,3]) return?','2','3','4','An error','B',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which is the correct way to declare an integer in C++?','integer x;','int x;','num x;','var x;','B',10 FROM skills s WHERE s.name='C++' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which operator accesses a member through an object pointer?','.','::','->','&','C',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which header provides std::vector?','<vector>','<array>','<list>','<map>','A',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which SQL clause filters rows before grouping?','ORDER BY','WHERE','HAVING','LIMIT','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which command reads rows from a table?','GET','READ','SELECT','OPEN','C',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which key uniquely identifies each row?','Foreign key','Primary key','Index only','View','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which HTML element creates a hyperlink?','<link>','<a>','<href>','<url>','B',10 FROM skills s WHERE s.name='HTML' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which attribute provides alternative text for an image?','title','src','alt','name','C',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which element is used for the main page heading?','<head>','<h1>','<header>','<title>','B',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword declares a block-scoped variable in JavaScript?','var only','let','dim','define','B',10 FROM skills s WHERE s.name='JavaScript' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which method converts JSON text into an object?','JSON.stringify','JSON.parse','JSON.object','JSON.read','B',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which array method adds an item to the end?','pop','shift','push','slice','C',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;


-- Candidate profile and skill-assessment extension. Additive and safe to rerun.
CREATE TABLE IF NOT EXISTS candidate_profiles (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  phone VARCHAR(25) NULL,
  experience VARCHAR(150) NULL,
  bio TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_education (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  degree VARCHAR(100) NULL,
  branch VARCHAR(120) NULL,
  college VARCHAR(200) NULL,
  graduation_year SMALLINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_education_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skills (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_skills (
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, skill_id),
  CONSTRAINT fk_candidate_skills_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_candidate_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_questions (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  skill_id INT UNSIGNED NOT NULL,
  question_text TEXT NOT NULL,
  option_a VARCHAR(500) NOT NULL,
  option_b VARCHAR(500) NOT NULL,
  option_c VARCHAR(500) NOT NULL,
  option_d VARCHAR(500) NOT NULL,
  correct_option CHAR(1) NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL DEFAULT 10,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_questions_skill_active (skill_id, active),
  CONSTRAINT fk_question_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  status ENUM('IN_PROGRESS','COMPLETED','TERMINATED') NOT NULL DEFAULT 'IN_PROGRESS',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  time_limit_seconds INT NOT NULL DEFAULT 900,
  score INT NOT NULL DEFAULT 0,
  total_marks INT NOT NULL DEFAULT 0,
  percentage DECIMAL(5,2) NULL,
  submitted_at DATETIME NULL,
  finish_reason VARCHAR(30) NULL,
  INDEX idx_attempt_user_skill (user_id, skill_id, status),
  CONSTRAINT fk_attempt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_attempt_questions (
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  question_number SMALLINT UNSIGNED NOT NULL,
  marks SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (attempt_id, question_id),
  UNIQUE KEY uq_attempt_question_number (attempt_id, question_number),
  CONSTRAINT fk_attempt_question_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_attempt_question_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_answers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL,
  question_id INT UNSIGNED NOT NULL,
  selected_answer CHAR(1) NULL,
  is_correct TINYINT(1) NOT NULL DEFAULT 0,
  marks_awarded SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  UNIQUE KEY uq_attempt_answer (attempt_id, question_id),
  CONSTRAINT fk_answer_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_answer_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_results (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT UNSIGNED NOT NULL UNIQUE,
  user_id INT UNSIGNED NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  score INT NOT NULL,
  total_marks INT NOT NULL,
  percentage DECIMAL(5,2) NOT NULL,
  correct_count INT NOT NULL,
  status ENUM('COMPLETED','TERMINATED') NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_result_user (user_id),
  CONSTRAINT fk_result_attempt FOREIGN KEY (attempt_id) REFERENCES assessment_attempts(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_result_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS skill_passports (
  user_id INT UNSIGNED NOT NULL PRIMARY KEY,
  passport_code VARCHAR(40) NOT NULL UNIQUE,
  generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_passport_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS candidate_projects (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  tech_stack VARCHAR(500),
  live_url VARCHAR(255),
  github_url VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_project_user (user_id),
  CONSTRAINT fk_project_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO skills(name) VALUES
('Python'),('C++'),('C'),('Java'),('JavaScript'),('HTML'),('CSS'),('SQL'),('MySQL'),('Data Structures & Algorithms'),('Machine Learning'),('Data Analysis'),('Git & GitHub'),('Flask');

-- Starter question bank (answers are stored server-side and never sent to the browser).
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword defines a function in Python?','func','def','function','lambda','B',10 FROM skills s WHERE s.name='Python' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which type is immutable in Python?','list','dict','set','tuple','D',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'What does len([1,2,3]) return?','2','3','4','An error','B',10 FROM skills s WHERE s.name='Python' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which is the correct way to declare an integer in C++?','integer x;','int x;','num x;','var x;','B',10 FROM skills s WHERE s.name='C++' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which operator accesses a member through an object pointer?','.','::','->','&','C',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which header provides std::vector?','<vector>','<array>','<list>','<map>','A',10 FROM skills s WHERE s.name='C++' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which SQL clause filters rows before grouping?','ORDER BY','WHERE','HAVING','LIMIT','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which command reads rows from a table?','GET','READ','SELECT','OPEN','C',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which key uniquely identifies each row?','Foreign key','Primary key','Index only','View','B',10 FROM skills s WHERE s.name IN ('SQL','MySQL') AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which HTML element creates a hyperlink?','<link>','<a>','<href>','<url>','B',10 FROM skills s WHERE s.name='HTML' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which attribute provides alternative text for an image?','title','src','alt','name','C',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which element is used for the main page heading?','<head>','<h1>','<header>','<title>','B',10 FROM skills s WHERE s.name='HTML' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which keyword declares a block-scoped variable in JavaScript?','var only','let','dim','define','B',10 FROM skills s WHERE s.name='JavaScript' AND NOT EXISTS(SELECT 1 FROM assessment_questions q WHERE q.skill_id=s.id);
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which method converts JSON text into an object?','JSON.stringify','JSON.parse','JSON.object','JSON.read','B',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<2;
INSERT INTO assessment_questions(skill_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks)
SELECT s.id,'Which array method adds an item to the end?','pop','shift','push','slice','C',10 FROM skills s WHERE s.name='JavaScript' AND (SELECT COUNT(*) FROM assessment_questions q WHERE q.skill_id=s.id)<3;
