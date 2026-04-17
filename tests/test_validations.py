"""Unit tests for form validation logic (validators.py)."""
from datetime import date, timedelta

import pytest

from validators import parse_date, validate_email, validate_task_form


class TestParseDate:
    def test_valid_date(self):
        d = parse_date("25/12/2030")
        assert d == date(2030, 12, 25)

    def test_invalid_format_returns_none(self):
        assert parse_date("2030-12-25") is None
        assert parse_date("32/01/2030") is None
        assert parse_date("abc") is None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_leading_zeros(self):
        assert parse_date("01/01/2030") == date(2030, 1, 1)


class TestValidateEmail:
    def test_valid_emails(self):
        assert validate_email("user@example.com") is True
        assert validate_email("first.last+tag@domain.co") is True

    def test_invalid_emails(self):
        assert validate_email("noatsign") is False
        assert validate_email("@nodomain.com") is False
        assert validate_email("missing@.com") is False
        assert validate_email("") is False
        assert validate_email(None) is False


class TestValidateTaskForm:
    FUTURE = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")
    PAST = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    def _base(self, **overrides):
        data = {
            "title": "Tarefa válida",
            "description": "",
            "deadline": self.FUTURE,
            "responsible_id": "1",
            "priority": "media",
            "status": "pendente",
        }
        data.update(overrides)
        return data

    def test_valid_form_passes(self):
        ok, errors = validate_task_form(**self._base())
        assert ok is True
        assert errors == {}

    def test_missing_title(self):
        ok, errors = validate_task_form(**self._base(title=""))
        assert ok is False
        assert "title" in errors

    def test_title_too_long(self):
        ok, errors = validate_task_form(**self._base(title="x" * 101))
        assert ok is False
        assert "title" in errors

    def test_description_too_long(self):
        ok, errors = validate_task_form(**self._base(description="d" * 501))
        assert ok is False
        assert "description" in errors

    def test_missing_deadline(self):
        ok, errors = validate_task_form(**self._base(deadline=""))
        assert ok is False
        assert "deadline" in errors

    def test_invalid_deadline_format(self):
        ok, errors = validate_task_form(**self._base(deadline="2030-01-01"))
        assert ok is False
        assert "deadline" in errors

    def test_past_deadline_rejected_for_new_task(self):
        ok, errors = validate_task_form(**self._base(deadline=self.PAST))
        assert ok is False
        assert "deadline" in errors

    def test_past_deadline_allowed_for_edit(self):
        ok, errors = validate_task_form(**self._base(deadline=self.PAST), is_edit=True)
        assert ok is True
        assert "deadline" not in errors

    def test_missing_responsible(self):
        ok, errors = validate_task_form(**self._base(responsible_id=""))
        assert ok is False
        assert "responsible_id" in errors

    def test_invalid_priority(self):
        ok, errors = validate_task_form(**self._base(priority="invalida"))
        assert ok is False
        assert "priority" in errors

    def test_invalid_status(self):
        ok, errors = validate_task_form(**self._base(status="feita"))
        assert ok is False
        assert "status" in errors

    def test_multiple_errors_reported(self):
        ok, errors = validate_task_form(**self._base(title="", deadline=""))
        assert ok is False
        assert "title" in errors
        assert "deadline" in errors
