ALTER SESSION SET CURRENT_SCHEMA = student_app;

CREATE OR REPLACE TRIGGER trg_grade_validate
BEFORE INSERT OR UPDATE OF student_id, discipline_id, grade ON grades
FOR EACH ROW
DECLARE
    v_report_type curriculum.report_type%TYPE;
BEGIN
    SELECT c.report_type INTO v_report_type
    FROM students s
    JOIN study_groups g ON g.group_id = s.group_id
    JOIN curriculum c ON c.specialty_id = g.specialty_id AND c.discipline_id = :NEW.discipline_id
    WHERE s.student_id = :NEW.student_id
    FETCH FIRST 1 ROW ONLY;

    IF v_report_type = 'экзамен' AND :NEW.grade NOT IN ('2','3','4','5') THEN
        RAISE_APPLICATION_ERROR(-20020, 'Для экзамена допустимы оценки 2, 3, 4 или 5');
    ELSIF v_report_type = 'зачет' AND :NEW.grade NOT IN ('зачет','незачет') THEN
        RAISE_APPLICATION_ERROR(-20021, 'Для зачета допустимы значения зачет или незачет');
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20022, 'Для студента не найден учебный план по выбранной дисциплине');
END;
/

CREATE OR REPLACE TRIGGER trg_students_audit
AFTER INSERT OR UPDATE ON students
FOR EACH ROW
BEGIN
    INSERT INTO audit_log(operation_type, entity_name, record_id, username, old_values, new_values)
    VALUES(CASE WHEN INSERTING THEN 'INSERT' ELSE 'UPDATE' END, 'STUDENTS', TO_CHAR(:NEW.student_id),
           NVL(SYS_CONTEXT('USERENV','CLIENT_IDENTIFIER'), SYS_CONTEXT('USERENV','SESSION_USER')),
           CASE WHEN UPDATING THEN 'name='||:OLD.last_name||' '||:OLD.first_name||';form='||:OLD.study_form||';group='||:OLD.group_id END,
           'name='||:NEW.last_name||' '||:NEW.first_name||';form='||:NEW.study_form||';group='||:NEW.group_id);
END;
/

CREATE OR REPLACE TRIGGER trg_curriculum_audit
AFTER INSERT OR UPDATE ON curriculum
FOR EACH ROW
BEGIN
    INSERT INTO audit_log(operation_type, entity_name, record_id, username, old_values, new_values)
    VALUES(CASE WHEN INSERTING THEN 'INSERT' ELSE 'UPDATE' END, 'CURRICULUM', TO_CHAR(:NEW.curriculum_id),
           NVL(SYS_CONTEXT('USERENV','CLIENT_IDENTIFIER'), SYS_CONTEXT('USERENV','SESSION_USER')),
           CASE WHEN UPDATING THEN 'specialty='||:OLD.specialty_id||';discipline='||:OLD.discipline_id||';semester='||:OLD.semester||';hours='||:OLD.hours||';report='||:OLD.report_type END,
           'specialty='||:NEW.specialty_id||';discipline='||:NEW.discipline_id||';semester='||:NEW.semester||';hours='||:NEW.hours||';report='||:NEW.report_type);
END;
/

CREATE OR REPLACE TRIGGER trg_grades_audit
AFTER INSERT OR UPDATE ON grades
FOR EACH ROW
BEGIN
    INSERT INTO audit_log(operation_type, entity_name, record_id, username, old_values, new_values)
    VALUES(CASE WHEN INSERTING THEN 'INSERT' ELSE 'UPDATE' END, 'GRADES', TO_CHAR(:NEW.grade_id),
           NVL(SYS_CONTEXT('USERENV','CLIENT_IDENTIFIER'), SYS_CONTEXT('USERENV','SESSION_USER')),
           CASE WHEN UPDATING THEN 'student='||:OLD.student_id||';discipline='||:OLD.discipline_id||';period='||:OLD.study_period||';grade='||:OLD.grade END,
           'student='||:NEW.student_id||';discipline='||:NEW.discipline_id||';period='||:NEW.study_period||';grade='||:NEW.grade);
END;
/
