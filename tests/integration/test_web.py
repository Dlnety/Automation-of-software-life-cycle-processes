"""Flask + настоящие функции db.py + Jinja: без подмены бизнес-логики, DEMO-хранилище."""
import pytest

import db


def text(response):
    return response.get_data(as_text=True)


def test_health(client):
    """/health доступен без входа и возвращает контракт HTTP 200 + JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"service": "StudentProgress", "status": "ok"}


@pytest.mark.parametrize("path", ["/", "/academic", "/academic/students",
    "/academic/students/1/edit", "/academic/curriculum", "/academic/curriculum/1/edit",
    "/teacher", "/teacher/grades", "/teacher/grades/1/edit"])
def test_anonymous_redirect(client, path):
    """Гость не может открыть защищённые страницы."""
    response = client.get(path)
    assert response.status_code == 302
    assert response.location == "/login"


@pytest.mark.parametrize("username, password, role, dashboard", [
    ("study", "study123", "academic", "/academic"),
    ("teacher", "teacher123", "teacher", "/teacher")])
def test_login_roles(client, username, password, role, dashboard):
    """Обе роли проходят настоящую проверку хэша и получают свою стартовую страницу."""
    response = client.post("/login", data=dict(username=f" {username} ", password=password))
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["username"] == username
        assert session["role"] == role
    assert client.get("/").location == dashboard
    assert client.get(dashboard).status_code == 200


@pytest.mark.parametrize("username, password", [("study", "wrong"), ("unknown", "study123"), ("", "")])
def test_bad_login(client, username, password):
    """Неверный пароль, неизвестный пользователь и пустая форма не дают сессию."""
    response = client.post("/login", data=dict(username=username, password=password))
    assert response.status_code == 200
    assert "Неверный логин или пароль." in text(response)
    with client.session_transaction() as session:
        assert "username" not in session


def test_logout(client, login):
    """Выход очищает сессию и снова закрывает защищённые страницы."""
    login()
    assert client.get("/logout").location == "/login"
    with client.session_transaction() as session:
        assert "username" not in session
    assert client.get("/academic/students").location == "/login"


@pytest.mark.parametrize("username, password, path", [
    ("teacher", "teacher123", "/academic/students"),
    ("teacher", "teacher123", "/academic/students/1/edit"),
    ("teacher", "teacher123", "/academic/curriculum"),
    ("teacher", "teacher123", "/academic/curriculum/1/edit"),
    ("study", "study123", "/teacher/grades"),
    ("study", "study123", "/teacher/grades/1/edit")])
def test_wrong_role_post(client, login, username, password, path):
    """POST другой роли запрещён и не меняет данные или аудит."""
    login(username, password)
    before = (db.list_students(), db.list_curriculum(), db.list_grades())
    response = client.post(path, data={})
    assert response.status_code == 302
    assert response.location == "/"
    assert (db.list_students(), db.list_curriculum(), db.list_grades()) == before
    assert db.DEMO_AUDIT == []
    assert "Недостаточно прав" in text(client.get("/", follow_redirects=True))


def test_academic_search(client, login):
    """Форма аналитики выводит число студентов и сведения о дисциплине."""
    login()
    response = client.post("/academic", data=dict(study_form="очная", discipline_name="базы данных"))
    body = text(response)
    assert response.status_code == 200
    assert '<div class="metric"><span>2</span>' in body
    assert "<dd>72</dd>" in body and "<dd>3</dd>" in body
    assert "09.03.04 — Программная инженерия" in body and "<dd>экзамен</dd>" in body
    assert db.count_students_by_form("очная") == 2
    assert db.get_discipline_info("базы данных")["semester"] == 3


def test_discipline_missing(client, login):
    """Неизвестная дисциплина даёт понятное сообщение."""
    login()
    response = client.post("/academic", data=dict(discipline_name="Несуществующая"))
    assert response.status_code == 200
    assert "Дисциплина не найдена." in text(response)


def test_student_create_edit(client, login, student_data):
    """Создание и редактирование студента проходят через HTTP и видны в списке; пишется аудит."""
    login()
    response = client.post("/academic/students", data=student_data)
    assert response.status_code == 302 and response.location == "/academic/students"
    new = db.list_students()[-1]
    assert new["last_name"] == "Казакова" and new["year"] == 2026
    assert "Казакова" in text(client.get(response.location))
    assert client.get(f'/academic/students/{new["id"]}/edit').status_code == 200
    student_data.update(last_name="Тихонкова", group_id="2", form="заочная")
    response = client.post(f'/academic/students/{new["id"]}/edit', data=student_data)
    assert response.status_code == 302
    updated = db.get_student(new["id"])
    assert updated["last_name"] == "Тихонкова"
    assert updated["group_id"] == 2 and updated["group_name"] == "231-322"
    assert updated["form"] == "заочная"
    assert db.DEMO_AUDIT == [
        dict(operation="INSERT", entity="STUDENTS", record_id=new["id"], username="study"),
        dict(operation="UPDATE", entity="STUDENTS", record_id=new["id"], username="study")]


def test_student_invalid_http(client, login, student_data):
    """HTTP-запрос с неверным годом показывает ошибку без сохранения."""
    login()
    student_data["year"] = "1999"
    before = db.list_students()
    response = client.post("/academic/students", data=student_data)
    assert response.status_code == 200
    assert "Год поступления" in text(response)
    assert db.list_students() == before and not db.DEMO_AUDIT


def test_curriculum_create_edit(client, login, curriculum_data):
    """Учебный план добавляется и редактируется, изменения и аудит сохраняются."""
    login()
    response = client.post("/academic/curriculum", data=curriculum_data)
    assert response.status_code == 302 and response.location == "/academic/curriculum"
    item = db.list_curriculum()[-1]
    assert item["hours"] == 144 and item["semester"] == 4
    assert "144" in text(client.get(response.location))
    assert client.get(f'/academic/curriculum/{item["id"]}/edit').status_code == 200
    curriculum_data.update(hours="180", report_type="зачет")
    response = client.post(f'/academic/curriculum/{item["id"]}/edit', data=curriculum_data)
    assert response.status_code == 302
    updated = db.get_curriculum(item["id"])
    assert updated["hours"] == 180 and updated["report_type"] == "зачет"
    assert [(r["operation"], r["entity"], r["username"]) for r in db.DEMO_AUDIT] == [
        ("INSERT", "CURRICULUM", "study"), ("UPDATE", "CURRICULUM", "study")]


def test_duplicate_curriculum(client, login, curriculum_data):
    """Повторный элемент плана отклоняется без второй записи и аудита."""
    login()
    assert client.post("/academic/curriculum", data=curriculum_data).status_code == 302
    before = db.list_curriculum()
    response = client.post("/academic/curriculum", data=curriculum_data)
    assert response.status_code == 200 and "уже существует" in text(response)
    assert db.list_curriculum() == before and len(db.DEMO_AUDIT) == 1


def test_grade_create_edit(client, login, grade_data):
    """Преподаватель добавляет и меняет оценку, журнал и аудит отражают результат."""
    login("teacher", "teacher123")
    response = client.post("/teacher/grades", data=grade_data)
    assert response.status_code == 302 and response.location == "/teacher/grades"
    item = db.list_grades()[-1]
    assert item["student_id"] == 3 and item["grade"] == "4"
    assert "Сидоров" in text(client.get(response.location))
    assert client.get(f'/teacher/grades/{item["id"]}/edit').status_code == 200
    response = client.post(f'/teacher/grades/{item["id"]}/edit', data=dict(grade="5"))
    assert response.status_code == 302
    assert db.get_grade(item["id"])["grade"] == "5"
    assert [(r["operation"], r["entity"], r["username"]) for r in db.DEMO_AUDIT] == [
        ("INSERT", "GRADES", "teacher"), ("UPDATE", "GRADES", "teacher")]


def test_duplicate_grade(client, login, grade_data):
    """Вторую оценку для той же тройки студент–дисциплина–период нельзя добавить."""
    login("teacher", "teacher123")
    assert client.post("/teacher/grades", data=grade_data).status_code == 302
    before = db.list_grades()
    response = client.post("/teacher/grades", data=grade_data)
    assert response.status_code == 200 and "оценка уже существует" in text(response)
    assert db.list_grades() == before and len(db.DEMO_AUDIT) == 1


def test_invalid_grade_http(client, login, grade_data):
    """Оценка 6 для экзамена отклоняется через HTTP без записи."""
    login("teacher", "teacher123")
    grade_data["grade"] = "6"
    before = db.list_grades()
    response = client.post("/teacher/grades", data=grade_data)
    assert response.status_code == 200 and "Недопустимая оценка" in text(response)
    assert db.list_grades() == before and not db.DEMO_AUDIT


@pytest.mark.parametrize("username, password, path, target, message", [
    ("study", "study123", "/academic/students/999/edit", "/academic/students", "Студент не найден"),
    ("study", "study123", "/academic/curriculum/999/edit", "/academic/curriculum", "Элемент учебного плана не найден"),
    ("teacher", "teacher123", "/teacher/grades/999/edit", "/teacher/grades", "Запись журнала не найдена")])
def test_missing_record(client, login, username, password, path, target, message):
    """Редактирование отсутствующей записи перенаправляет в список с сообщением."""
    login(username, password)
    response = client.get(path)
    assert response.status_code == 302 and response.location == target
    assert message in text(client.get(target))
