from models import Produto
from extensions import db as _db
from tests.conftest import cria_empresa, cria_admin, login


def test_produto_requer_login(client):

    resposta = client.get("/produtos/")

    assert resposta.status_code in (302, 401)


def test_criar_produto(client, app):

    with app.app_context():
        empresa = cria_empresa()
        cria_admin(empresa)

    login(client)

    client.post(
        "/produtos/novo",
        data={
            "nome": "Notebook",
            "codigo": "NB001",
            "quantidade_atual": "10",
            "quantidade_minima": "2"
        },
        follow_redirects=True
    )

    with app.app_context():

        produto = Produto.query.filter_by(
            codigo="NB001"
        ).first()

        assert produto is not None
        assert produto.nome == "Notebook"


def test_listar_produtos(client, app):

    with app.app_context():

        empresa = cria_empresa()
        cria_admin(empresa)

        produto = Produto(
            empresa_id=empresa.id,
            nome="Mouse",
            codigo="M001"
        )

        _db.session.add(produto)
        _db.session.commit()

    login(client)

    resposta = client.get("/produtos/")

    assert resposta.status_code == 200
    assert b"Mouse" in resposta.data