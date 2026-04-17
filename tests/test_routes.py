"""Integration tests for Flask routes."""
from datetime import date, timedelta

import pytest

from models import Task, User, db
from tests.conftest import login_as


FUTURE = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")


# ── Auth routes ───────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_page_loads(self, client):
        r = client.get("/login")
        assert r.status_code == 200
        assert b"E-mail" in r.data

    def test_redirect_root_to_login(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 302

    def test_login_success(self, client, seed_users):
        r = login_as(client, "admin@test.com", "admin123")
        assert r.status_code == 200
        assert "Login realizado".encode() in r.data

    def test_login_wrong_password(self, client, seed_users):
        r = login_as(client, "admin@test.com", "wrong")
        assert r.status_code == 200
        assert b"incorretos" in r.data

    def test_login_unknown_email(self, client, seed_users):
        r = login_as(client, "nobody@test.com", "pass")
        assert r.status_code == 200
        assert b"incorretos" in r.data

    def test_login_invalid_email_format(self, client, seed_users):
        r = login_as(client, "notanemail", "pass")
        assert r.status_code == 200
        assert b"inv" in r.data.lower()

    def test_login_missing_fields(self, client, seed_users):
        r = client.post("/login", data={}, follow_redirects=True)
        assert r.status_code == 200
        assert b"obrigat" in r.data

    def test_logout(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/logout", follow_redirects=True)
        assert b"Logout" in r.data


class TestForgotPassword:
    def test_forgot_password_page_loads(self, client):
        r = client.get("/forgot-password")
        assert r.status_code == 200

    def test_forgot_password_valid_email(self, client):
        r = client.post(
            "/forgot-password", data={"email": "user@example.com"}, follow_redirects=True
        )
        assert b"instru" in r.data

    def test_forgot_password_invalid_email(self, client):
        r = client.post(
            "/forgot-password", data={"email": "notvalid"}, follow_redirects=True
        )
        assert b"v" in r.data.lower()  # "válido" in flash message


# ── Dashboard ────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_requires_login(self, client):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code == 302

    def test_dashboard_loads_after_login(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/dashboard")
        assert r.status_code == 200
        assert b"Painel" in r.data

    def test_dashboard_shows_tasks(self, client, seed_users):
        admin = seed_users["admin"]
        aluno = seed_users["aluno"]
        task = Task(
            title="Dashboard Task",
            deadline=date.today() + timedelta(days=5),
            responsible_id=aluno.id,
            created_by_id=admin.id,
            priority="alta",
            status="pendente",
        )
        db.session.add(task)
        db.session.commit()

        login_as(client, "admin@test.com", "admin123")
        r = client.get("/dashboard")
        assert b"Dashboard Task" in r.data


# ── Task CRUD ─────────────────────────────────────────────────────────────────

class TestNewTask:
    def test_new_task_page_loads(self, client, seed_users):
        login_as(client, "aluno@test.com", "aluno123")
        r = client.get("/tasks/new")
        assert r.status_code == 200
        assert b"Nova Tarefa" in r.data

    def test_create_task_valid(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        aluno = seed_users["aluno"]
        r = client.post(
            "/tasks/new",
            data={
                "title": "Integration Test Task",
                "description": "Created in test",
                "deadline": FUTURE,
                "responsible_id": str(aluno.id),
                "priority": "media",
                "status": "pendente",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"criada com sucesso" in r.data
        assert Task.query.filter_by(title="Integration Test Task").first() is not None

    def test_create_task_missing_title(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        aluno = seed_users["aluno"]
        r = client.post(
            "/tasks/new",
            data={
                "title": "",
                "deadline": FUTURE,
                "responsible_id": str(aluno.id),
                "priority": "media",
                "status": "pendente",
            },
        )
        assert r.status_code == 200
        assert b"obrigat" in r.data

    def test_create_task_invalid_deadline_format(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        aluno = seed_users["aluno"]
        r = client.post(
            "/tasks/new",
            data={
                "title": "Bad Deadline",
                "deadline": "2030/01/01",
                "responsible_id": str(aluno.id),
                "priority": "media",
                "status": "pendente",
            },
        )
        assert r.status_code == 200
        assert b"inv" in r.data.lower()

    def test_create_task_past_deadline(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        aluno = seed_users["aluno"]
        past = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        r = client.post(
            "/tasks/new",
            data={
                "title": "Past Task",
                "deadline": past,
                "responsible_id": str(aluno.id),
                "priority": "media",
                "status": "pendente",
            },
        )
        assert r.status_code == 200
        assert b"futura" in r.data or b"atual" in r.data


class TestEditTask:
    def _create_task(self, users):
        task = Task(
            title="Edit Me",
            deadline=date.today() + timedelta(days=5),
            responsible_id=users["aluno"].id,
            created_by_id=users["admin"].id,
            priority="baixa",
            status="pendente",
        )
        db.session.add(task)
        db.session.commit()
        return task

    def test_edit_task_page_loads(self, client, seed_users):
        task = self._create_task(seed_users)
        login_as(client, "admin@test.com", "admin123")
        r = client.get(f"/tasks/{task.id}/edit")
        assert r.status_code == 200
        assert b"Edit Me" in r.data

    def test_edit_task_updates_title(self, client, seed_users):
        task = self._create_task(seed_users)
        login_as(client, "admin@test.com", "admin123")
        r = client.post(
            f"/tasks/{task.id}/edit",
            data={
                "title": "Updated Title",
                "deadline": FUTURE,
                "responsible_id": str(seed_users["aluno"].id),
                "priority": "alta",
                "status": "em_andamento",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"atualizada com sucesso" in r.data
        db.session.refresh(task)
        assert task.title == "Updated Title"

    def test_edit_task_404_for_nonexistent(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/tasks/99999/edit")
        assert r.status_code == 404


class TestDeleteTask:
    def _create_task(self, users):
        task = Task(
            title="Delete Me",
            deadline=date.today() + timedelta(days=5),
            responsible_id=users["aluno"].id,
            created_by_id=users["admin"].id,
            priority="baixa",
            status="pendente",
        )
        db.session.add(task)
        db.session.commit()
        return task

    def test_admin_can_delete(self, client, seed_users):
        task = self._create_task(seed_users)
        login_as(client, "admin@test.com", "admin123")
        r = client.post(f"/tasks/{task.id}/delete", follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(Task, task.id) is None

    def test_professor_can_delete(self, client, seed_users):
        task = self._create_task(seed_users)
        login_as(client, "prof@test.com", "prof123")
        r = client.post(f"/tasks/{task.id}/delete", follow_redirects=True)
        assert r.status_code == 200

    def test_aluno_cannot_delete(self, client, seed_users):
        task = self._create_task(seed_users)
        login_as(client, "aluno@test.com", "aluno123")
        r = client.post(f"/tasks/{task.id}/delete")
        assert r.status_code == 403


class TestUpdateStatus:
    def test_update_status(self, client, seed_users):
        task = Task(
            title="Status Task",
            deadline=date.today() + timedelta(days=5),
            responsible_id=seed_users["aluno"].id,
            created_by_id=seed_users["admin"].id,
            priority="media",
            status="pendente",
        )
        db.session.add(task)
        db.session.commit()

        login_as(client, "admin@test.com", "admin123")
        r = client.post(
            f"/tasks/{task.id}/status",
            data={"status": "concluida"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        db.session.refresh(task)
        assert task.status == "concluida"

    def test_invalid_status_returns_400(self, client, seed_users):
        task = Task(
            title="Status Task 2",
            deadline=date.today() + timedelta(days=5),
            responsible_id=seed_users["aluno"].id,
            created_by_id=seed_users["admin"].id,
            priority="media",
            status="pendente",
        )
        db.session.add(task)
        db.session.commit()

        login_as(client, "admin@test.com", "admin123")
        r = client.post(f"/tasks/{task.id}/status", data={"status": "invalido"})
        assert r.status_code == 400


# ── Reports ───────────────────────────────────────────────────────────────────

class TestReports:
    def test_reports_page_loads(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/reports")
        assert r.status_code == 200
        assert b"Relat" in r.data

    def test_export_csv(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/reports/export/csv")
        assert r.status_code == 200
        assert "text/csv" in r.content_type
        assert b"ID" in r.data  # CSV header

    def test_export_pdf(self, client, seed_users):
        login_as(client, "admin@test.com", "admin123")
        r = client.get("/reports/export/pdf")
        assert r.status_code == 200
        assert "application/pdf" in r.content_type
        assert r.data[:4] == b"%PDF"  # PDF magic bytes
