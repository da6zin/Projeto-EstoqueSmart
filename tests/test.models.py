from models import Usuario, Produto


def test_senha_hash():

    usuario = Usuario(
        nome="Teste",
        email="teste@teste.com",
        cargo="admin",
        empresa_id=1
    )

    usuario.set_senha("123456")

    assert usuario.senha_hash != "123456"


def test_checar_senha():

    usuario = Usuario(
        nome="Teste",
        email="teste@teste.com",
        cargo="admin",
        empresa_id=1
    )

    usuario.set_senha("123456")

    assert usuario.checar_senha("123456") is True


def test_estoque_critico():

    produto = Produto(
        nome="Caneta",
        codigo="C01",
        empresa_id=1,
        quantidade_atual=2,
        quantidade_minima=5
    )

    assert produto.estoque_critico is True