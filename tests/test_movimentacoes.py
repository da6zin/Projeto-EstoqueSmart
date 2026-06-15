from models import Produto
from extensions import db as _db
from tests.conftest import cria_empresa, cria_admin, login


def test_entrada_aumenta_estoque(client, app):

    with app.app_context():

        empresa = cria_empresa()
        cria_admin(empresa)

        produto = Produto(
            empresa_id=empresa.id,
            nome="Teclado",
            codigo="T001",
            quantidade_atual=10
        )

        _db.session.add(produto)
        _db.session.commit()

        pid = produto.id

    login(client)

    client.post(
        f"/movimentacoes/registrar/{pid}",
        data={
            "tipo": "entrada",
            "quantidade": "5"
        },
        follow_redirects=True
    )

    with app.app_context():

        produto = _db.session.get(
            Produto,
            pid
        )

        assert produto.quantidade_atual == 15


def test_saida_diminui_estoque(client, app):

    with app.app_context():

        empresa = cria_empresa()
        cria_admin(empresa)

        produto = Produto(
            empresa_id=empresa.id,
            nome="Monitor",
            codigo="MON01",
            quantidade_atual=10
        )

        _db.session.add(produto)
        _db.session.commit()

        pid = produto.id

    login(client)

    client.post(
        f"/movimentacoes/registrar/{pid}",
        data={
            "tipo": "saida",
            "quantidade": "3"
        },
        follow_redirects=True
    )

    with app.app_context():

        produto = _db.session.get(
            Produto,
            pid
        )

        assert produto.quantidade_atual == 7