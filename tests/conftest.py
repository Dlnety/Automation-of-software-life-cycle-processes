"""Изоляция DEMO-данных: каждый тест получает исходное состояние."""
from copy import deepcopy

import pytest

import app as web
import db


@pytest.fixture(autouse=True)
def isolated_demo(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    # Даже при случайном переключении режима тесты не подключатся к реальной БД.
    def no_connection(*args, **kwargs):
        raise AssertionError("Реальная Oracle не используется в этом наборе тестов")
    monkeypatch.setattr(db, "get_connection", no_connection)
    for name in ("DEMO_SPECIALTIES", "DEMO_GROUPS", "DEMO_STUDENTS",
                 "DEMO_DISCIPLINES", "DEMO_CURRICULUM", "DEMO_GRADES",
                 "DEMO_AUDIT", "DEMO_USERS"):
        monkeypatch.setattr(db, name, deepcopy(getattr(db, name)))
    monkeypatch.setitem(web.app.config, "TESTING", True)
    monkeypatch.setitem(web.app.config, "SECRET_KEY", "lr7-test-session-key")


@pytest.fixture
def client():
    return web.app.test_client()


@pytest.fixture
def student_data():
    return dict(last_name="Казакова", first_name="Диана", middle_name="",
                year="2026", form="очная", group_id="1")


@pytest.fixture
def curriculum_data():
    return dict(specialty_id="1", discipline_id="2", semester="4",
                hours="144", report_type="экзамен")


@pytest.fixture
def grade_data():
    return dict(student_id="3", discipline_id="1",
                period="2026/2027, семестр 3", grade="4")


@pytest.fixture
def login(client):
    def do_login(username="study", password="study123"):
        response = client.post("/login", data={"username": username, "password": password})
        assert response.status_code == 302
        assert response.location == "/"
        return response
    return do_login
