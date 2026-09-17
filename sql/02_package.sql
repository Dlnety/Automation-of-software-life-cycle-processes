ALTER SESSION SET CURRENT_SCHEMA = student_app;

CREATE OR REPLACE PACKAGE STUDENT_PROGRESS_PKG AS
    FUNCTION count_students_by_form(p_form IN VARCHAR2) RETURN NUMBER;
    PROCEDURE get_discipline_info(p_discipline IN VARCHAR2, p_hours OUT NUMBER, p_semester OUT NUMBER, p_specialty OUT VARCHAR2, p_report_type OUT VARCHAR2);
    PROCEDURE add_student(p_last_name IN VARCHAR2, p_first_name IN VARCHAR2, p_middle_name IN VARCHAR2, p_admission_year IN NUMBER, p_study_form IN VARCHAR2, p_group_id IN NUMBER);
    PROCEDURE update_student(p_student_id IN NUMBER, p_last_name IN VARCHAR2, p_first_name IN VARCHAR2, p_middle_name IN VARCHAR2, p_admission_year IN NUMBER, p_study_form IN VARCHAR2, p_group_id IN NUMBER);
    PROCEDURE add_curriculum(p_specialty_id IN NUMBER, p_discipline_id IN NUMBER, p_semester IN NUMBER, p_hours IN NUMBER, p_report_type IN VARCHAR2);
    PROCEDURE update_curriculum(p_curriculum_id IN NUMBER, p_specialty_id IN NUMBER, p_discipline_id IN NUMBER, p_semester IN NUMBER, p_hours IN NUMBER, p_report_type IN VARCHAR2);
    PROCEDURE add_grade(p_student_id IN NUMBER, p_discipline_id IN NUMBER, p_study_period IN VARCHAR2, p_grade IN VARCHAR2);
    PROCEDURE update_grade(p_grade_id IN NUMBER, p_grade IN VARCHAR2);
END STUDENT_PROGRESS_PKG;
/

CREATE OR REPLACE PACKAGE BODY STUDENT_PROGRESS_PKG AS
    PROCEDURE validate_study_form(p_form IN VARCHAR2) IS
    BEGIN
        IF p_form NOT IN ('очная', 'очно-заочная', 'заочная') THEN
            RAISE_APPLICATION_ERROR(-20010, 'Недопустимая форма обучения');
        END IF;
    END;

    FUNCTION count_students_by_form(p_form IN VARCHAR2) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        validate_study_form(p_form);
        SELECT COUNT(*) INTO v_count FROM students WHERE study_form = p_form;
        RETURN v_count;
    END;

    PROCEDURE get_discipline_info(p_discipline IN VARCHAR2, p_hours OUT NUMBER, p_semester OUT NUMBER, p_specialty OUT VARCHAR2, p_report_type OUT VARCHAR2) IS
    BEGIN
        SELECT c.hours, c.semester, s.code || ' — ' || s.name, c.report_type
        INTO p_hours, p_semester, p_specialty, p_report_type
        FROM curriculum c
        JOIN disciplines d ON d.discipline_id = c.discipline_id
        JOIN specialties s ON s.specialty_id = c.specialty_id
        WHERE LOWER(d.name) = LOWER(TRIM(p_discipline))
        FETCH FIRST 1 ROW ONLY;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20001, 'Дисциплина не найдена');
    END;

    PROCEDURE add_student(p_last_name IN VARCHAR2, p_first_name IN VARCHAR2, p_middle_name IN VARCHAR2, p_admission_year IN NUMBER, p_study_form IN VARCHAR2, p_group_id IN NUMBER) IS
    BEGIN
        validate_study_form(p_study_form);
        IF p_admission_year NOT BETWEEN 2000 AND 2100 THEN RAISE_APPLICATION_ERROR(-20011, 'Некорректный год поступления'); END IF;
        INSERT INTO students(last_name, first_name, middle_name, admission_year, study_form, group_id)
        VALUES(TRIM(p_last_name), TRIM(p_first_name), TRIM(p_middle_name), p_admission_year, p_study_form, p_group_id);
    END;

    PROCEDURE update_student(p_student_id IN NUMBER, p_last_name IN VARCHAR2, p_first_name IN VARCHAR2, p_middle_name IN VARCHAR2, p_admission_year IN NUMBER, p_study_form IN VARCHAR2, p_group_id IN NUMBER) IS
    BEGIN
        validate_study_form(p_study_form);
        UPDATE students SET last_name=TRIM(p_last_name), first_name=TRIM(p_first_name), middle_name=TRIM(p_middle_name), admission_year=p_admission_year, study_form=p_study_form, group_id=p_group_id
        WHERE student_id=p_student_id;
        IF SQL%ROWCOUNT=0 THEN RAISE_APPLICATION_ERROR(-20002, 'Студент не найден'); END IF;
    END;

    PROCEDURE add_curriculum(p_specialty_id IN NUMBER, p_discipline_id IN NUMBER, p_semester IN NUMBER, p_hours IN NUMBER, p_report_type IN VARCHAR2) IS
    BEGIN
        IF p_semester NOT BETWEEN 1 AND 12 THEN RAISE_APPLICATION_ERROR(-20012, 'Семестр должен быть от 1 до 12'); END IF;
        IF p_hours <= 0 THEN RAISE_APPLICATION_ERROR(-20013, 'Количество часов должно быть положительным'); END IF;
        IF p_report_type NOT IN ('экзамен','зачет') THEN RAISE_APPLICATION_ERROR(-20014, 'Недопустимая форма отчётности'); END IF;
        INSERT INTO curriculum(specialty_id, discipline_id, semester, hours, report_type)
        VALUES(p_specialty_id, p_discipline_id, p_semester, p_hours, p_report_type);
    EXCEPTION WHEN DUP_VAL_ON_INDEX THEN RAISE_APPLICATION_ERROR(-20015, 'Такой элемент учебного плана уже существует');
    END;

    PROCEDURE update_curriculum(p_curriculum_id IN NUMBER, p_specialty_id IN NUMBER, p_discipline_id IN NUMBER, p_semester IN NUMBER, p_hours IN NUMBER, p_report_type IN VARCHAR2) IS
    BEGIN
        IF p_semester NOT BETWEEN 1 AND 12 THEN RAISE_APPLICATION_ERROR(-20012, 'Семестр должен быть от 1 до 12'); END IF;
        IF p_hours <= 0 THEN RAISE_APPLICATION_ERROR(-20013, 'Количество часов должно быть положительным'); END IF;
        IF p_report_type NOT IN ('экзамен','зачет') THEN RAISE_APPLICATION_ERROR(-20014, 'Недопустимая форма отчётности'); END IF;
        UPDATE curriculum SET specialty_id=p_specialty_id, discipline_id=p_discipline_id, semester=p_semester, hours=p_hours, report_type=p_report_type
        WHERE curriculum_id=p_curriculum_id;
        IF SQL%ROWCOUNT=0 THEN RAISE_APPLICATION_ERROR(-20016, 'Элемент учебного плана не найден'); END IF;
    END;

    PROCEDURE add_grade(p_student_id IN NUMBER, p_discipline_id IN NUMBER, p_study_period IN VARCHAR2, p_grade IN VARCHAR2) IS
    BEGIN
        INSERT INTO grades(student_id, discipline_id, study_period, grade)
        VALUES(p_student_id, p_discipline_id, TRIM(p_study_period), LOWER(TRIM(p_grade)));
    EXCEPTION WHEN DUP_VAL_ON_INDEX THEN RAISE_APPLICATION_ERROR(-20003, 'Оценка для этого студента, дисциплины и периода уже существует');
    END;

    PROCEDURE update_grade(p_grade_id IN NUMBER, p_grade IN VARCHAR2) IS
    BEGIN
        UPDATE grades SET grade=LOWER(TRIM(p_grade)) WHERE grade_id=p_grade_id;
        IF SQL%ROWCOUNT=0 THEN RAISE_APPLICATION_ERROR(-20004, 'Запись журнала не найдена'); END IF;
    END;
END STUDENT_PROGRESS_PKG;
/
