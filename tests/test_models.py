"""Unit tests for SQLAlchemy models (User and Task)."""
from datetime import date, timedelta

import pytest

from models import Task, User


class TestUser:
    def test_password_hashing(self, clean_db):
        u = User(name="Test", email="t@t.com", role="aluno")
        u.set_password("secret")
        assert u.password_hash != "secret"
        assert u.check_password("secret") is True

    def test_wrong_password_rejected(self, clean_db):
        u = User(name="Test", email="t2@t.com", role="aluno")
        u.set_password("correct")
        assert u.check_password("wrong") is False

    def test_default_role_is_aluno(self, clean_db, db):
        u = User(name="NoRole", email="norole@t.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()
        assert u.role == "aluno"

    def test_repr(self, clean_db):
        u = User(name="A", email="repr@t.com", role="admin")
        u.set_password("x")
        assert "repr@t.com" in repr(u)


class TestTask:
    def _make_task(self, db, users, days=5, status="pendente", priority="media"):
        task = Task(
            title="Test Task",
            description="A description",
            deadline=date.today() + timedelta(days=days),
            responsible_id=users["aluno"].id,
            created_by_id=users["admin"].id,
            priority=priority,
            status=status,
        )
        db.session.add(task)
        db.session.commit()
        return task

    def test_status_label_pendente(self, db, seed_users):
        t = self._make_task(db, seed_users, status="pendente")
        assert t.status_label == "Pendente"

    def test_status_label_em_andamento(self, db, seed_users):
        t = self._make_task(db, seed_users, status="em_andamento")
        assert t.status_label == "Em andamento"

    def test_status_label_concluida(self, db, seed_users):
        t = self._make_task(db, seed_users, status="concluida")
        assert t.status_label == "Concluída"

    def test_priority_label_alta(self, db, seed_users):
        t = self._make_task(db, seed_users, priority="alta")
        assert t.priority_label == "Alta"

    def test_priority_label_baixa(self, db, seed_users):
        t = self._make_task(db, seed_users, priority="baixa")
        assert t.priority_label == "Baixa"

    def test_deadline_str_format(self, db, seed_users):
        t = self._make_task(db, seed_users, days=10)
        # Should be formatted as DD/MM/YYYY
        parts = t.deadline_str.split("/")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # day
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 4  # year

    def test_is_overdue_future_task(self, db, seed_users):
        t = self._make_task(db, seed_users, days=5, status="pendente")
        assert t.is_overdue is False

    def test_is_overdue_past_task(self, db, seed_users):
        t = self._make_task(db, seed_users, days=-2, status="pendente")
        assert t.is_overdue is True

    def test_is_not_overdue_when_concluida(self, db, seed_users):
        t = self._make_task(db, seed_users, days=-2, status="concluida")
        assert t.is_overdue is False

    def test_repr(self, db, seed_users):
        t = self._make_task(db, seed_users)
        assert "Test Task" in repr(t)
