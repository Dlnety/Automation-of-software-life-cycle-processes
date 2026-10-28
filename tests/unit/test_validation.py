"""Юнит-тесты отдельных функций db.py."""
import hashlib

import pytest

import db


def test_password_correct_and_wrong():
    """PBKDF2: верный пароль принимается, неверный отклоняется."""
    salt = b"lr7-test-salt"
    digest = hashlib.pbkdf2_hmac("sha256", b"test-password", salt, 1000).hex()
    stored = f"pbkdf2_sha256$1000${salt.hex()}${digest}"
    assert db.verify_password("test-password", stored)
    assert not db.verify_password("wrong", stored)


@pytest.mark.parametrize("stored", ["", "broken", "sha1$1000$aa$bb",
                                     "pbkdf2_sha256$abc$aa$bb",
                                     "pbkdf2_sha256$1000$zz$bb",
                                     "pbkdf2_sha256$0$aa$bb"])
def test_password_malformed(stored):
    """Повреждённые хэши не приводят к успешному входу или исключению."""
    assert db.verify_password("test-password", stored) is False


@pytest.mark.parametrize("rows, expected", [([], 1), ([{"id": 7}, {"id": 2}], 8)])
def test_next_id(rows, expected):
    """Идентификатор больше максимального, для пустой таблицы равен 1."""
    assert db._next_id(rows) == expected


@pytest.mark.parametrize("middle, expected", [("Иванович", "Иванов Иван Иванович"),
                                             ("", "Иванов Иван"), (None, "Иванов Иван")])
def test_full_name(middle, expected):
    """ФИО собирается без лишнего пробела при отсутствии отчества."""
    assert db._full_name(dict(last_name="Иванов", first_name="Иван", middle_name=middle)) == expected


@pytest.mark.parametrize("field, value, message", [
    ("semester", "0", "Семестр"), ("semester", "13", "Семестр"),
    ("hours", "0", "Количество часов"), ("hours", "-1", "Количество часов"),
    ("report_type", "контрольная", "форма отчётности")])
def test_curriculum_invalid(curriculum_data, field, value, message):
    """Семестр вне 1–12, неположительные часы и неизвестная отчётность отклоняются."""
    curriculum_data[field] = value
    with pytest.raises(ValueError, match=message):
        db._validate_curriculum(curriculum_data)


@pytest.mark.parametrize("semester", ["1", "12"])
def test_curriculum_boundaries(curriculum_data, semester):
    """Граничные допустимые семестры 1 и 12 принимаются."""
    curriculum_data.update(semester=semester, hours="1", report_type="зачет")
    db._validate_curriculum(curriculum_data)


@pytest.mark.parametrize("field, value, message", [
    ("form", "дистанционная", "форма обучения"),
    ("year", "1999", "Год поступления"), ("year", "2101", "Год поступления"),
    ("group_id", "999", "группа не найдена")])
def test_invalid_student_no_write(student_data, field, value, message):
    """Некорректный студент отклоняется без записи студента и аудита."""
    student_data[field] = value
    before = db.list_students()
    with pytest.raises(ValueError, match=message):
        db.add_student(student_data, "study")
    assert db.list_students() == before
    assert db.DEMO_AUDIT == []


@pytest.mark.parametrize("form, expected", [("очная", 2), ("очно-заочная", 1), ("заочная", 0)])
def test_count_students(form, expected):
    """Подсчёт по каждой допустимой форме соответствует исходным данным."""
    assert db.count_students_by_form(form) == expected


def test_count_rejects_unknown_form():
    """Подсчёт отклоняет неизвестную форму обучения."""
    with pytest.raises(ValueError, match="форму обучения"):
        db.count_students_by_form("неизвестная")


@pytest.mark.parametrize("student, discipline, grade", [(1, 1, "2"), (1, 1, "5"),
                                                        (2, 1, "зачет"), (2, 1, "незачет")])
def test_valid_grade(student, discipline, grade):
    """Экзамен принимает 2–5, зачёт принимает зачет/незачет."""
    db._validate_demo_grade(student, discipline, grade)


@pytest.mark.parametrize("student, discipline, grade", [(1, 1, "1"), (1, 1, "6"),
    (1, 1, "зачет"), (2, 1, "5"), (999, 1, "5"), (1, 999, "5")])
def test_invalid_grade(student, discipline, grade):
    """Неверная шкала, отсутствующий студент или учебный план отклоняются."""
    with pytest.raises(ValueError):
        db._validate_demo_grade(student, discipline, grade)


@pytest.mark.parametrize("text, expected", [
    ("ORA-20001: Дисциплина отсутствует\nORA-06512: details", "Дисциплина отсутствует"),
    ("ORA-00001: details", "Такая запись уже существует."),
    ("ORA-02291: details", "Не найден связанный объект. Проверьте выбранные значения."),
    ("ORA-02290: details", "Одно из значений не соответствует допустимым ограничениям."),
    ("internal connection info", "Операцию выполнить не удалось. Проверьте введённые данные.")])
def test_friendly_error(text, expected):
    """Ошибки Oracle преобразуются в понятные сообщения без внутренних деталей."""
    assert db.friendly_db_error(Exception(text)) == expected
