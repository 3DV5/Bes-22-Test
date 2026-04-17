import csv
import io
import os
from datetime import date, datetime
from urllib.parse import urljoin, urlsplit

from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import case

from models import Task, User, db
from validators import parse_date, validate_email, validate_task_form


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///taskmanager.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config:
        app.config.update(config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_safe_url(target):
        """Return True only if target points to the same host (no open redirect)."""
        ref = urlsplit(request.host_url)
        dest = urlsplit(urljoin(request.host_url, target))
        return dest.scheme in ("http", "https") and ref.netloc == dest.netloc

    def _apply_task_filters(query):
        """Apply URL query-string filters to a Task query."""
        f_status = request.args.get("status", "")
        f_priority = request.args.get("priority", "")
        f_responsible = request.args.get("responsible", "")
        date_from_str = request.args.get("date_from", "")
        date_to_str = request.args.get("date_to", "")

        if f_status:
            query = query.filter(Task.status == f_status)
        if f_priority:
            query = query.filter(Task.priority == f_priority)
        if f_responsible:
            query = query.filter(Task.responsible_id == f_responsible)

        date_from = parse_date(date_from_str) if date_from_str else None
        date_to = parse_date(date_to_str) if date_to_str else None
        if date_from:
            query = query.filter(Task.deadline >= date_from)
        if date_to:
            query = query.filter(Task.deadline <= date_to)

        return query

    # ── Auth routes ───────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        errors = {}
        email = ""
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email:
                errors["email"] = "E-mail é obrigatório."
            elif not validate_email(email):
                errors["email"] = "Formato de e-mail inválido."

            if not password:
                errors["password"] = "Senha é obrigatória."

            if not errors:
                user = User.query.filter_by(email=email).first()
                if user and user.check_password(password):
                    login_user(user, remember=request.form.get("remember") == "on")
                    next_page = request.args.get("next")
                    if not next_page or not _is_safe_url(next_page):
                        next_page = url_for("dashboard")
                    flash("Login realizado com sucesso!", "success")
                    return redirect(next_page)
                errors["general"] = "E-mail ou senha incorretos."

        return render_template("login.html", errors=errors, email=email)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logout realizado com sucesso.", "info")
        return redirect(url_for("login"))

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        message = None
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            if email and validate_email(email):
                message = (
                    f"Se o e-mail {email} estiver cadastrado, "
                    "você receberá as instruções em breve."
                )
            else:
                flash("Informe um e-mail válido.", "danger")
        return render_template("forgot_password.html", message=message)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    @app.route("/dashboard")
    @login_required
    def dashboard():
        query = Task.query
        query = _apply_task_filters(query)

        sort_by = request.args.get("sort", "deadline")
        if sort_by == "title":
            query = query.order_by(Task.title)
        elif sort_by == "priority":
            priority_order = case(
                (Task.priority == "alta", 1),
                (Task.priority == "media", 2),
                (Task.priority == "baixa", 3),
                else_=4,
            )
            query = query.order_by(priority_order)
        elif sort_by == "status":
            query = query.order_by(Task.status)
        else:
            query = query.order_by(Task.deadline)

        tasks = query.all()
        users = User.query.order_by(User.name).all()

        counts = {
            "total": Task.query.count(),
            "pendente": Task.query.filter_by(status="pendente").count(),
            "em_andamento": Task.query.filter_by(status="em_andamento").count(),
            "concluida": Task.query.filter_by(status="concluida").count(),
        }

        return render_template(
            "dashboard.html",
            tasks=tasks,
            users=users,
            counts=counts,
            filter_status=request.args.get("status", ""),
            filter_priority=request.args.get("priority", ""),
            filter_responsible=request.args.get("responsible", ""),
            sort_by=sort_by,
            today=date.today(),
        )

    # ── Task CRUD ─────────────────────────────────────────────────────────────

    @app.route("/tasks/new", methods=["GET", "POST"])
    @login_required
    def new_task():
        users = User.query.order_by(User.name).all()
        form_data = {}
        errors = {}

        if request.method == "POST":
            form_data = _collect_form_data()
            valid, errors = validate_task_form(**form_data)
            if valid:
                task = Task(
                    title=form_data["title"],
                    description=form_data["description"] or None,
                    deadline=parse_date(form_data["deadline"]),
                    responsible_id=int(form_data["responsible_id"]),
                    created_by_id=current_user.id,
                    priority=form_data["priority"],
                    status=form_data["status"],
                )
                db.session.add(task)
                db.session.commit()
                flash("Tarefa criada com sucesso!", "success")
                return redirect(url_for("dashboard"))

        return render_template(
            "task_form.html",
            users=users,
            form_data=form_data,
            errors=errors,
            editing=False,
        )

    @app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_task(task_id):
        task = db.session.get(Task, task_id)
        if task is None:
            abort(404)
        users = User.query.order_by(User.name).all()
        errors = {}

        if request.method == "POST":
            form_data = _collect_form_data()
            valid, errors = validate_task_form(**form_data, is_edit=True)
            if valid:
                task.title = form_data["title"]
                task.description = form_data["description"] or None
                task.deadline = parse_date(form_data["deadline"])
                task.responsible_id = int(form_data["responsible_id"])
                task.priority = form_data["priority"]
                task.status = form_data["status"]
                task.updated_at = datetime.utcnow()
                db.session.commit()
                flash("Tarefa atualizada com sucesso!", "success")
                return redirect(url_for("dashboard"))
        else:
            form_data = {
                "title": task.title,
                "description": task.description or "",
                "deadline": task.deadline_str,
                "responsible_id": str(task.responsible_id),
                "priority": task.priority,
                "status": task.status,
            }

        return render_template(
            "task_form.html",
            task=task,
            users=users,
            form_data=form_data,
            errors=errors,
            editing=True,
        )

    @app.route("/tasks/<int:task_id>/delete", methods=["POST"])
    @login_required
    def delete_task(task_id):
        if current_user.role not in ("admin", "professor"):
            abort(403)
        task = db.session.get(Task, task_id)
        if task is None:
            abort(404)
        db.session.delete(task)
        db.session.commit()
        flash("Tarefa removida.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/tasks/<int:task_id>/status", methods=["POST"])
    @login_required
    def update_status(task_id):
        task = db.session.get(Task, task_id)
        if task is None:
            abort(404)
        new_status = request.form.get("status", "")
        if new_status not in Task.STATUS_CHOICES:
            abort(400)
        task.status = new_status
        task.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Status atualizado para "{task.status_label}".', "success")
        referrer = request.referrer
        if referrer and _is_safe_url(referrer):
            return redirect(referrer)
        return redirect(url_for("dashboard"))

    # ── Reports ───────────────────────────────────────────────────────────────

    @app.route("/reports")
    @login_required
    def reports():
        query = _apply_task_filters(Task.query)
        tasks = query.order_by(Task.deadline).all()
        users = User.query.order_by(User.name).all()

        return render_template(
            "reports.html",
            tasks=tasks,
            users=users,
            filter_responsible=request.args.get("responsible", ""),
            filter_priority=request.args.get("priority", ""),
            filter_status=request.args.get("status", ""),
            date_from=request.args.get("date_from", ""),
            date_to=request.args.get("date_to", ""),
        )

    @app.route("/reports/export/csv")
    @login_required
    def export_csv():
        tasks = _apply_task_filters(Task.query).order_by(Task.deadline).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["ID", "Título", "Descrição", "Prazo", "Responsável", "Prioridade", "Status", "Criado em"]
        )
        for task in tasks:
            writer.writerow(
                [
                    task.id,
                    task.title,
                    task.description or "",
                    task.deadline_str,
                    task.responsible.name if task.responsible else "",
                    task.priority_label,
                    task.status_label,
                    task.created_at.strftime("%d/%m/%Y %H:%M"),
                ]
            )

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment;filename=tarefas.csv"},
        )

    @app.route("/reports/export/pdf")
    @login_required
    def export_pdf():
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        tasks = _apply_task_filters(Task.query).order_by(Task.deadline).all()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm,
        )
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Relatório de Tarefas", styles["Title"]),
            Paragraph(
                f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
                styles["Normal"],
            ),
            Spacer(1, 0.5 * cm),
        ]

        header = ["ID", "Título", "Prazo", "Responsável", "Prioridade", "Status"]
        data = [header] + [
            [
                str(task.id),
                task.title[:45],
                task.deadline_str,
                (task.responsible.name[:25] if task.responsible else ""),
                task.priority_label,
                task.status_label,
            ]
            for task in tasks
        ]

        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(data)):
            bg = colors.white if i % 2 == 0 else colors.HexColor("#f8f9fa")
            table_style.append(("BACKGROUND", (0, i), (-1, i), bg))

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle(table_style))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="tarefas.pdf",
        )

    # ── Error handlers ────────────────────────────────────────────────────────

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    # ── CLI commands ──────────────────────────────────────────────────────────

    @app.cli.command("init-db")
    def init_db_cmd():
        """Create database tables."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db_cmd():
        """Populate the database with sample data."""
        from datetime import timedelta

        db.create_all()
        users_data = [
            ("Administrador", "admin@test.com", "admin", "admin123"),
            ("Professor Silva", "professor@test.com", "professor", "prof123"),
            ("Aluno João", "aluno@test.com", "aluno", "aluno123"),
        ]
        created_users = []
        for name, email, role, pwd in users_data:
            if not User.query.filter_by(email=email).first():
                u = User(name=name, email=email, role=role)
                u.set_password(pwd)
                db.session.add(u)
                created_users.append(u)
        db.session.flush()

        admin = User.query.filter_by(email="admin@test.com").first()
        aluno = User.query.filter_by(email="aluno@test.com").first()
        if admin and aluno and Task.query.count() == 0:
            tasks_data = [
                ("Configurar ambiente de testes", "Instalar pytest e dependências", 3, "baixa", "concluida"),
                ("Escrever casos de teste unitários", "Cobrir modelos e validações", 7, "media", "em_andamento"),
                ("Implementar testes de integração", "Fluxo completo de criação de tarefa", 14, "alta", "pendente"),
                ("Documentar o projeto", "README e comentários no código", 10, "baixa", "pendente"),
            ]
            for title, desc, days, priority, status in tasks_data:
                task = Task(
                    title=title,
                    description=desc,
                    deadline=date.today() + timedelta(days=days),
                    responsible_id=aluno.id,
                    created_by_id=admin.id,
                    priority=priority,
                    status=status,
                )
                db.session.add(task)

        db.session.commit()
        print("Seed data created successfully.")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _collect_form_data():
        return {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "deadline": request.form.get("deadline", "").strip(),
            "responsible_id": request.form.get("responsible_id", ""),
            "priority": request.form.get("priority", "media"),
            "status": request.form.get("status", "pendente"),
        }

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
