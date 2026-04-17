import pytest
from flask import g
from sqlalchemy.pool import StaticPool

from app import create_app
from models import Task, User, db as _db


@pytest.fixture(scope="session")
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Flask 2.x stores g in the app context (not request context).
    # Flask-Login caches the loaded user in g._login_user and skips
    # re-loading if the attribute already exists.  With a persistent test
    # app context this cache leaks across requests/tests.  Clearing it
    # before each request forces Flask-Login to reload from the session.
    @application.before_request
    def _clear_login_user_cache():
        if hasattr(g, "_login_user"):
            delattr(g, "_login_user")

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="session")
def db(app):
    return _db


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture()
def clean_db(db):
    """Truncate all rows before each test that requests this fixture."""
    db.session.query(Task).delete()
    db.session.query(User).delete()
    db.session.commit()
    yield db
    db.session.query(Task).delete()
    db.session.query(User).delete()
    db.session.commit()


@pytest.fixture()
def seed_users(clean_db):
    """Create three users (admin, professor, aluno) and return them."""
    admin = User(name="Admin Test", email="admin@test.com", role="admin")
    admin.set_password("admin123")

    prof = User(name="Professor Test", email="prof@test.com", role="professor")
    prof.set_password("prof123")

    aluno = User(name="Aluno Test", email="aluno@test.com", role="aluno")
    aluno.set_password("aluno123")

    clean_db.session.add_all([admin, prof, aluno])
    clean_db.session.commit()
    return {"admin": admin, "prof": prof, "aluno": aluno}


def login_as(client, email, password):
    return client.post(
        "/login", data={"email": email, "password": password}, follow_redirects=True
    )
