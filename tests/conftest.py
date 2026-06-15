import pytest
import secrets
from unittest.mock import patch

from app import create_app
from extensions import db as _db
from models import Empresa, Usuario


@pytest.fixture
def app():
    # Ignora a migração manual durante os testes
    with patch('app._migrar_banco'):
        app = create_app()

        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SECRET_KEY="teste"
        )

        with app.app_context():
            _db.create_all()
            yield app
            _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def limpar_banco(app):
    with app.app_context():
        for tabela in reversed(_db.metadata.sorted_tables):
            _db.session.execute(tabela.delete())
        _db.session.commit()


def cria_empresa():
    empresa = Empresa(
        nome="Empresa Teste",
        codigo_convite=secrets.token_hex(4).upper()
    )

    _db.session.add(empresa)
    _db.session.commit()

    return empresa


def cria_admin(empresa):
    usuario = Usuario(
        nome="Admin",
        email="admin@teste.com",
        cargo="admin",
        empresa_id=empresa.id
    )

    usuario.set_senha("senha123")

    _db.session.add(usuario)
    _db.session.commit()

    return usuario


def login(client):
    return client.post(
        "/auth/login",
        data={
            "email": "admin@teste.com",
            "senha": "senha123"
        },
        follow_redirects=True
    )