import hashlib
import hmac
import os
import re
from copy import deepcopy

import oracledb
from dotenv import load_dotenv

load_dotenv()

STUDY_FORMS = ("очная", "очно-заочная", "заочная")
REPORT_TYPES = ("экзамен", "зачет")


def demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "1") == "1"


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверка хэша формата pbkdf2_sha256$iterations$salt$hash."""
    try:
        algorithm, iterations, salt_hex, expected_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected_hex)
    except (ValueError, TypeError):
        return False


def get_connection(username: str | None = None):
    conn = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN"),
    )
    if username:
        with conn.cursor() as cur:
            cur.callproc("DBMS_SESSION.SET_IDENTIFIER", [username])
    return conn


def friendly_db_error(exc: Exception) -> str:
    text = str(exc)
    match = re.search(r"ORA-20\d{3}:\s*([^\n]+)", text)
    if match:
        return match.group(1).strip()
    if "ORA-00001" in text:
        return "Такая запись уже существует."
    if "ORA-02291" in text:
        return "Не найден связанный объект. Проверьте выбранные значения."
    if "ORA-02290" in text:
        return "Одно из значений не соответствует допустимым ограничениям."
    return "Операцию выполнить не удалось. Проверьте введённые данные."


DEMO_SPECIALTIES = [
    {"id": 1, "code": "09.03.04", "name": "Программная инженерия"},
    {"id": 2, "code": "09.03.01", "name": "Информатика и вычислительная техника"},
]
DEMO_GROUPS = [
    {"id": 1, "name": "241-321", "specialty_id": 1, "specialty": "09.03.04 — Программная инженерия"},
    {"id": 2, "name": "231-322", "specialty_id": 2, "specialty": "09.03.01 — Информатика и вычислительная техника"},
]
DEMO_STUDENTS = [
    {"id": 1, "last_name": "Иванов", "first_name": "Иван", "middle_name": "Иванович", "year": 2024, "form": "очная", "group_id": 1, "group_name": "241-321"},
    {"id": 2, "last_name": "Петрова", "first_name": "Анна", "middle_name": "Сергеевна", "year": 2023, "form": "очно-заочная", "group_id": 2, "group_name": "231-322"},
    {"id": 3, "last_name": "Сидоров", "first_name": "Максим", "middle_name": "Олегович", "year": 2024, "form": "очная", "group_id": 1, "group_name": "241-321"},
]
DEMO_DISCIPLINES = [
    {"id": 1, "name": "Базы данных"},
    {"id": 2, "name": "Программирование"},
]
DEMO_CURRICULUM = [
    {"id": 1, "specialty_id": 1, "specialty": "09.03.04 — Программная инженерия", "discipline_id": 1, "discipline": "Базы данных", "semester": 3, "hours": 72, "report_type": "экзамен"},
    {"id": 2, "specialty_id": 1, "specialty": "09.03.04 — Программная инженерия", "discipline_id": 2, "discipline": "Программирование", "semester": 2, "hours": 108, "report_type": "экзамен"},
    {"id": 3, "specialty_id": 2, "specialty": "09.03.01 — Информатика и вычислительная техника", "discipline_id": 1, "discipline": "Базы данных", "semester": 3, "hours": 72, "report_type": "зачет"},
]
DEMO_GRADES = [
    {"id": 1, "student_id": 1, "student": "Иванов Иван Иванович", "discipline_id": 1, "discipline": "Базы данных", "period": "2026/2027, семестр 3", "grade": "5"}
]
DEMO_AUDIT = []
DEMO_USERS = {
    "study": {"password_hash": "pbkdf2_sha256$260000$a1b2c3d4e5f60718293a4b5c6d7e8f90$428b10dfeff08f0c41dfaa94079fde6bd97a2a41024a013b06b89083bb2b95bc", "role": "academic", "title": "Учебный отдел"},
    "teacher": {"password_hash": "pbkdf2_sha256$260000$1029384756aabbccddeeff0011223344$179c76b5deefeb226f1987ce78bcc743579319e4138869aed0e4be68f1d04794", "role": "teacher", "title": "Преподаватель"},
}


def _next_id(rows):
    return max((int(r["id"]) for r in rows), default=0) + 1


def _full_name(student):
    return " ".join(p for p in [student["last_name"], student["first_name"], student.get("middle_name")] if p)


def authenticate(username: str, password: str):
    if demo_mode():
        user = DEMO_USERS.get(username)
        if user and verify_password(password, user["password_hash"]):
            return {"username": username, "role": user["role"], "title": user["title"]}
        return None

    with get_connection(username) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash, role FROM app_users WHERE username = :username",
                {"username": username},
            )
            row = cur.fetchone()
    if row and verify_password(password, row[0]):
        title = "Учебный отдел" if row[1] == "academic" else "Преподаватель"
        return {"username": username, "role": row[1], "title": title}
    return None


def list_specialties():
    if demo_mode():
        return deepcopy(DEMO_SPECIALTIES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT specialty_id, code, name FROM specialties ORDER BY code")
        return [{"id": r[0], "code": r[1], "name": r[2]} for r in cur]


def list_groups():
    if demo_mode():
        return deepcopy(DEMO_GROUPS)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT g.group_id, g.group_name, s.specialty_id, s.code || ' — ' || s.name
            FROM study_groups g JOIN specialties s ON s.specialty_id = g.specialty_id
            ORDER BY g.group_name
        """)
        return [{"id": r[0], "name": r[1], "specialty_id": r[2], "specialty": r[3]} for r in cur]


def list_disciplines():
    if demo_mode():
        return deepcopy(DEMO_DISCIPLINES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT discipline_id, name FROM disciplines ORDER BY name")
        return [{"id": r[0], "name": r[1]} for r in cur]


def list_students():
    if demo_mode():
        return deepcopy(DEMO_STUDENTS)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT s.student_id, s.last_name, s.first_name, s.middle_name,
                   s.admission_year, s.study_form, s.group_id, g.group_name
            FROM students s JOIN study_groups g ON g.group_id = s.group_id
            ORDER BY s.last_name, s.first_name
        """)
        return [{"id": r[0], "last_name": r[1], "first_name": r[2], "middle_name": r[3],
                 "year": r[4], "form": r[5], "group_id": r[6], "group_name": r[7]} for r in cur]


def get_student(student_id: int):
    return next((s for s in list_students() if int(s["id"]) == int(student_id)), None)


def count_students_by_form(study_form: str) -> int:
    if study_form not in STUDY_FORMS:
        raise ValueError("Выберите допустимую форму обучения.")
    if demo_mode():
        return sum(1 for s in DEMO_STUDENTS if s["form"] == study_form)
    with get_connection() as conn, conn.cursor() as cur:
        result = cur.callfunc("STUDENT_PROGRESS_PKG.count_students_by_form", int, [study_form])
        return int(result)


def get_discipline_info(name: str):
    if demo_mode():
        for item in DEMO_CURRICULUM:
            if item["discipline"].lower() == name.lower():
                return deepcopy(item)
        return None
    with get_connection() as conn, conn.cursor() as cur:
        hours = cur.var(int)
        semester = cur.var(int)
        specialty = cur.var(str, size=250)
        report_type = cur.var(str, size=30)
        try:
            cur.callproc("STUDENT_PROGRESS_PKG.get_discipline_info", [name, hours, semester, specialty, report_type])
        except oracledb.DatabaseError as exc:
            if "ORA-20001" in str(exc):
                return None
            raise
        return {"discipline": name, "hours": hours.getvalue(), "semester": semester.getvalue(),
                "specialty": specialty.getvalue(), "report_type": report_type.getvalue()}


def add_student(data, username):
    if data["form"] not in STUDY_FORMS:
        raise ValueError("Недопустимая форма обучения.")
    if int(data["year"]) < 2000 or int(data["year"]) > 2100:
        raise ValueError("Год поступления должен быть в диапазоне 2000–2100.")
    if demo_mode():
        group = next((g for g in DEMO_GROUPS if g["id"] == int(data["group_id"])), None)
        if not group:
            raise ValueError("Учебная группа не найдена.")
        row = {"id": _next_id(DEMO_STUDENTS), "last_name": data["last_name"].strip(),
               "first_name": data["first_name"].strip(), "middle_name": data.get("middle_name", "").strip(),
               "year": int(data["year"]), "form": data["form"], "group_id": int(data["group_id"]),
               "group_name": group["name"]}
        DEMO_STUDENTS.append(row)
        DEMO_AUDIT.append({"operation": "INSERT", "entity": "STUDENTS", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.add_student", [data["last_name"], data["first_name"], data.get("middle_name") or None,
                                                               int(data["year"]), data["form"], int(data["group_id"])])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def update_student(student_id, data, username):
    if data["form"] not in STUDY_FORMS:
        raise ValueError("Недопустимая форма обучения.")
    if demo_mode():
        row = next((s for s in DEMO_STUDENTS if s["id"] == int(student_id)), None)
        group = next((g for g in DEMO_GROUPS if g["id"] == int(data["group_id"])), None)
        if not row or not group:
            raise ValueError("Студент или группа не найдены.")
        row.update(last_name=data["last_name"].strip(), first_name=data["first_name"].strip(), middle_name=data.get("middle_name", "").strip(),
                   year=int(data["year"]), form=data["form"], group_id=int(data["group_id"]), group_name=group["name"])
        DEMO_AUDIT.append({"operation": "UPDATE", "entity": "STUDENTS", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.update_student", [int(student_id), data["last_name"], data["first_name"], data.get("middle_name") or None,
                                                                  int(data["year"]), data["form"], int(data["group_id"])])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def list_curriculum():
    if demo_mode():
        return deepcopy(DEMO_CURRICULUM)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.curriculum_id, c.specialty_id, s.code || ' — ' || s.name,
                   c.discipline_id, d.name, c.semester, c.hours, c.report_type
            FROM curriculum c
            JOIN specialties s ON s.specialty_id = c.specialty_id
            JOIN disciplines d ON d.discipline_id = c.discipline_id
            ORDER BY s.code, c.semester, d.name
        """)
        return [{"id": r[0], "specialty_id": r[1], "specialty": r[2], "discipline_id": r[3], "discipline": r[4],
                 "semester": r[5], "hours": r[6], "report_type": r[7]} for r in cur]


def get_curriculum(curriculum_id: int):
    return next((c for c in list_curriculum() if int(c["id"]) == int(curriculum_id)), None)


def _validate_curriculum(data):
    if int(data["semester"]) not in range(1, 13):
        raise ValueError("Семестр должен быть от 1 до 12.")
    if int(data["hours"]) <= 0:
        raise ValueError("Количество часов должно быть положительным.")
    if data["report_type"] not in REPORT_TYPES:
        raise ValueError("Недопустимая форма отчётности.")


def add_curriculum(data, username):
    _validate_curriculum(data)
    if demo_mode():
        if any(c["specialty_id"] == int(data["specialty_id"]) and c["discipline_id"] == int(data["discipline_id"]) and c["semester"] == int(data["semester"]) for c in DEMO_CURRICULUM):
            raise ValueError("Такой элемент учебного плана уже существует.")
        sp = next((s for s in DEMO_SPECIALTIES if s["id"] == int(data["specialty_id"])), None)
        ds = next((d for d in DEMO_DISCIPLINES if d["id"] == int(data["discipline_id"])), None)
        if not sp or not ds: raise ValueError("Специальность или дисциплина не найдена.")
        row = {"id": _next_id(DEMO_CURRICULUM), "specialty_id": sp["id"], "specialty": f'{sp["code"]} — {sp["name"]}',
               "discipline_id": ds["id"], "discipline": ds["name"], "semester": int(data["semester"]),
               "hours": int(data["hours"]), "report_type": data["report_type"]}
        DEMO_CURRICULUM.append(row)
        DEMO_AUDIT.append({"operation": "INSERT", "entity": "CURRICULUM", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.add_curriculum", [int(data["specialty_id"]), int(data["discipline_id"]), int(data["semester"]), int(data["hours"]), data["report_type"]])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def update_curriculum(curriculum_id, data, username):
    _validate_curriculum(data)
    if demo_mode():
        row = next((c for c in DEMO_CURRICULUM if c["id"] == int(curriculum_id)), None)
        sp = next((s for s in DEMO_SPECIALTIES if s["id"] == int(data["specialty_id"])), None)
        ds = next((d for d in DEMO_DISCIPLINES if d["id"] == int(data["discipline_id"])), None)
        if not row or not sp or not ds: raise ValueError("Элемент учебного плана не найден.")
        row.update(specialty_id=sp["id"], specialty=f'{sp["code"]} — {sp["name"]}', discipline_id=ds["id"], discipline=ds["name"],
                   semester=int(data["semester"]), hours=int(data["hours"]), report_type=data["report_type"])
        DEMO_AUDIT.append({"operation": "UPDATE", "entity": "CURRICULUM", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.update_curriculum", [int(curriculum_id), int(data["specialty_id"]), int(data["discipline_id"]), int(data["semester"]), int(data["hours"]), data["report_type"]])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def list_grades():
    if demo_mode():
        return deepcopy(DEMO_GRADES)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT g.grade_id, g.student_id,
                   s.last_name || ' ' || s.first_name || ' ' || NVL(s.middle_name, ''),
                   g.discipline_id, d.name, g.study_period, g.grade
            FROM grades g
            JOIN students s ON s.student_id = g.student_id
            JOIN disciplines d ON d.discipline_id = g.discipline_id
            ORDER BY s.last_name, d.name, g.study_period
        """)
        return [{"id": r[0], "student_id": r[1], "student": r[2].strip(), "discipline_id": r[3], "discipline": r[4], "period": r[5], "grade": r[6]} for r in cur]


def get_grade(grade_id: int):
    return next((g for g in list_grades() if int(g["id"]) == int(grade_id)), None)


def _validate_demo_grade(student_id, discipline_id, grade):
    student = next((s for s in DEMO_STUDENTS if s["id"] == int(student_id)), None)
    group = next((g for g in DEMO_GROUPS if student and g["id"] == student["group_id"]), None)
    plan = next((c for c in DEMO_CURRICULUM if group and c["specialty_id"] == group["specialty_id"] and c["discipline_id"] == int(discipline_id)), None)
    if not plan:
        raise ValueError("Для студента не найден учебный план по выбранной дисциплине.")
    allowed = {"2", "3", "4", "5"} if plan["report_type"] == "экзамен" else {"зачет", "незачет"}
    if grade not in allowed:
        raise ValueError(f'Недопустимая оценка для формы отчётности «{plan["report_type"]}».')


def add_grade(data, username):
    if demo_mode():
        _validate_demo_grade(data["student_id"], data["discipline_id"], data["grade"])
        if any(g["student_id"] == int(data["student_id"]) and g["discipline_id"] == int(data["discipline_id"]) and g["period"] == data["period"].strip() for g in DEMO_GRADES):
            raise ValueError("Для этого студента, дисциплины и периода оценка уже существует.")
        student = next(s for s in DEMO_STUDENTS if s["id"] == int(data["student_id"]))
        discipline = next(d for d in DEMO_DISCIPLINES if d["id"] == int(data["discipline_id"]))
        row = {"id": _next_id(DEMO_GRADES), "student_id": student["id"], "student": _full_name(student), "discipline_id": discipline["id"],
               "discipline": discipline["name"], "period": data["period"].strip(), "grade": data["grade"]}
        DEMO_GRADES.append(row)
        DEMO_AUDIT.append({"operation": "INSERT", "entity": "GRADES", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.add_grade", [int(data["student_id"]), int(data["discipline_id"]), data["period"], data["grade"]])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def update_grade(grade_id, data, username):
    if demo_mode():
        row = next((g for g in DEMO_GRADES if g["id"] == int(grade_id)), None)
        if not row: raise ValueError("Запись журнала не найдена.")
        _validate_demo_grade(row["student_id"], row["discipline_id"], data["grade"])
        row["grade"] = data["grade"]
        DEMO_AUDIT.append({"operation": "UPDATE", "entity": "GRADES", "record_id": row["id"], "username": username})
        return
    conn = get_connection(username)
    try:
        with conn.cursor() as cur:
            cur.callproc("STUDENT_PROGRESS_PKG.update_grade", [int(grade_id), data["grade"]])
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()
