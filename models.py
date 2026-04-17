from datetime import date, datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLES = ["aluno", "professor", "admin"]

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="aluno")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks_created = db.relationship(
        "Task", foreign_keys="Task.created_by_id", backref="creator", lazy=True
    )
    tasks_assigned = db.relationship(
        "Task", foreign_keys="Task.responsible_id", backref="responsible", lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Task(db.Model):
    __tablename__ = "tasks"

    STATUS_CHOICES = ["pendente", "em_andamento", "concluida"]
    STATUS_LABELS = {
        "pendente": "Pendente",
        "em_andamento": "Em andamento",
        "concluida": "Concluída",
    }
    PRIORITY_CHOICES = ["baixa", "media", "alta"]
    PRIORITY_LABELS = {"baixa": "Baixa", "media": "Média", "alta": "Alta"}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    deadline = db.Column(db.Date, nullable=False)
    responsible_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="media")
    status = db.Column(db.String(20), nullable=False, default="pendente")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def priority_label(self):
        return self.PRIORITY_LABELS.get(self.priority, self.priority)

    @property
    def deadline_str(self):
        return self.deadline.strftime("%d/%m/%Y") if self.deadline else ""

    @property
    def is_overdue(self):
        return self.deadline < date.today() and self.status != "concluida"

    def __repr__(self):
        return f"<Task {self.title}>"
