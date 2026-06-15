from models import Empresa, Usuario
from extensions import db as _db

def test_cadastro_admin_cria_empresa(client, app):

    client.post(
        "/auth/cadastro",
        data={
            "nome": "João",
            "email": "joao@teste.com",
            "senha": "123456",
            "confirmar": "123456",
            "cargo": "admin",
            "nome_empresa": "Minha Empresa"
        },
        follow_redirects=True
    )

    with app.app_context():

        usuario = Usuario.query.filter_by(
            email="joao@teste.com"
        ).first()

        assert usuario is not None
        assert usuario.cargo == "admin"

        empresa = _db.session.get(
            Empresa,
            usuario.empresa_id
        )

        assert empresa.nome == "Minha Empresa"


def test_login_funciona(client, app):

    from tests.conftest import cria_empresa, cria_admin, login

    with app.app_context():
        empresa = cria_empresa()
        cria_admin(empresa)

    resposta = login(client)

    assert resposta.status_code == 200


def test_logout(client, app):

    from tests.conftest import cria_empresa, cria_admin, login

    with app.app_context():
        empresa = cria_empresa()
        cria_admin(empresa)

    login(client)

    resposta = client.get(
        "/auth/logout",
        follow_redirects=True
    )

    assert resposta.status_code == 200