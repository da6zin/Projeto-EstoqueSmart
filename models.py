from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    cargo = db.Column(db.String(20), nullable=False, default='funcionario')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.cargo == 'admin'

    def __repr__(self):
        return f'<Usuario {self.email}>'


class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20))
    contato = db.Column(db.String(100))
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    endereco = db.Column(db.String(255))
    observacao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Fornecedor {self.nome}>'


class Produto(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(50), nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False, default=0)
    quantidade_minima = db.Column(db.Integer, nullable=False, default=5)
    preco_custo = db.Column(db.Numeric(10, 2), nullable=True)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    movimentacoes = db.relationship('Movimentacao', backref='produto', lazy=True, cascade='all, delete-orphan')
    fornecedor = db.relationship('Fornecedor', backref='produtos')

    @property
    def estoque_critico(self):
        return self.quantidade_atual <= self.quantidade_minima

    def __repr__(self):
        return f'<Produto {self.nome}>'


class Movimentacao(db.Model):
    __tablename__ = 'movimentacoes'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=True)
    observacao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def valor_total(self):
        if self.preco_unitario is not None:
            return float(self.preco_unitario) * self.quantidade
        return None

    def __repr__(self):
        return f'<Movimentacao {self.tipo} {self.quantidade}>'


class Empresa(db.Model):
    __tablename__ = 'empresas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo_convite = db.Column(db.String(20), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuarios = db.relationship('Usuario', backref='empresa', lazy=True)
