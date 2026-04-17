import re
from datetime import date, datetime


def parse_date(date_str):
    """Parse a date from DD/MM/AAAA format. Returns a date object or None."""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def validate_email(email):
    """Return True if email has a valid format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email or ""))


def validate_task_form(
    title, description, deadline, responsible_id, priority, status, is_edit=False
):
    """Validate task form data.

    Returns (is_valid: bool, errors: dict).
    When is_edit=True the deadline is allowed to be a past date (format is
    still validated).
    """
    from models import Task  # local import to avoid circular deps

    errors = {}

    # Title – required, 1–100 chars
    if not title or not title.strip():
        errors["title"] = "Título é obrigatório."
    elif len(title.strip()) > 100:
        errors["title"] = "Título deve ter no máximo 100 caracteres."

    # Description – optional, max 500 chars
    if description and len(description) > 500:
        errors["description"] = "Descrição deve ter no máximo 500 caracteres."

    # Deadline – required, DD/MM/AAAA format, future date (new tasks only)
    if not deadline or not str(deadline).strip():
        errors["deadline"] = "Prazo é obrigatório."
    else:
        parsed = parse_date(str(deadline))
        if parsed is None:
            errors["deadline"] = "Formato de prazo inválido. Use DD/MM/AAAA."
        elif not is_edit and parsed < date.today():
            errors["deadline"] = "O prazo deve ser uma data atual ou futura."

    # Responsible – required
    if not responsible_id:
        errors["responsible_id"] = "Responsável é obrigatório."

    # Priority – must be a valid choice
    if priority not in Task.PRIORITY_CHOICES:
        errors["priority"] = "Prioridade inválida."

    # Status – must be a valid choice
    if status not in Task.STATUS_CHOICES:
        errors["status"] = "Status inválido."

    return len(errors) == 0, errors
