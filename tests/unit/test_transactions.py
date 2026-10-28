"""Проверка Python-ветки Oracle с подменой подключения, не самой СУБД."""
from unittest.mock import MagicMock

import pytest

import db


@pytest.mark.parametrize("failure", [False, True])
def test_add_student_transaction(monkeypatch, student_data, failure):
    """Oracle-адаптер передаёт параметры, делает commit либо rollback и закрывает соединение."""
    monkeypatch.setenv("DEMO_MODE", "0")
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    connection_factory = MagicMock(return_value=connection)
    monkeypatch.setattr(db, "get_connection", connection_factory)
    if failure:
        cursor.callproc.side_effect = RuntimeError("test database failure")
        with pytest.raises(RuntimeError, match="test database failure"):
            db.add_student(student_data, "study")
        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()
    else:
        db.add_student(student_data, "study")
        connection.commit.assert_called_once_with()
        connection.rollback.assert_not_called()
    connection_factory.assert_called_once_with("study")
    cursor.callproc.assert_called_once_with("STUDENT_PROGRESS_PKG.add_student",
        ["Казакова", "Диана", None, 2026, "очная", 1])
    connection.close.assert_called_once_with()
