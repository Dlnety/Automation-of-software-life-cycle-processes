ALTER SESSION SET CURRENT_SCHEMA = student_app;

INSERT INTO specialties(specialty_id, code, name) VALUES(1, '09.03.04', 'Программная инженерия');
INSERT INTO specialties(specialty_id, code, name) VALUES(2, '09.03.01', 'Информатика и вычислительная техника');
INSERT INTO study_groups(group_id, group_name, specialty_id) VALUES(1, '241-321', 1);
INSERT INTO study_groups(group_id, group_name, specialty_id) VALUES(2, '231-322', 2);
INSERT INTO students(student_id,last_name,first_name,middle_name,admission_year,study_form,group_id) VALUES(1,'Иванов','Иван','Иванович',2024,'очная',1);
INSERT INTO students(student_id,last_name,first_name,middle_name,admission_year,study_form,group_id) VALUES(2,'Петрова','Анна','Сергеевна',2023,'очно-заочная',2);
INSERT INTO students(student_id,last_name,first_name,middle_name,admission_year,study_form,group_id) VALUES(3,'Сидоров','Максим','Олегович',2024,'очная',1);
INSERT INTO disciplines(discipline_id,name) VALUES(1,'Базы данных');
INSERT INTO disciplines(discipline_id,name) VALUES(2,'Программирование');
INSERT INTO curriculum(curriculum_id,specialty_id,discipline_id,semester,hours,report_type) VALUES(1,1,1,3,72,'экзамен');
INSERT INTO curriculum(curriculum_id,specialty_id,discipline_id,semester,hours,report_type) VALUES(2,1,2,2,108,'экзамен');
INSERT INTO curriculum(curriculum_id,specialty_id,discipline_id,semester,hours,report_type) VALUES(3,2,1,3,72,'зачет');
INSERT INTO grades(grade_id,student_id,discipline_id,study_period,grade) VALUES(1,1,1,'2026/2027, семестр 3','5');
INSERT INTO app_users(user_id,username,password_hash,role) VALUES(1,'study','pbkdf2_sha256$260000$a1b2c3d4e5f60718293a4b5c6d7e8f90$428b10dfeff08f0c41dfaa94079fde6bd97a2a41024a013b06b89083bb2b95bc','academic');
INSERT INTO app_users(user_id,username,password_hash,role) VALUES(2,'teacher','pbkdf2_sha256$260000$1029384756aabbccddeeff0011223344$179c76b5deefeb226f1987ce78bcc743579319e4138869aed0e4be68f1d04794','teacher');
COMMIT;
