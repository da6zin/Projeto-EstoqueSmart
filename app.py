import os
from dotenv import load_dotenv
from flask import Flask, render_template
from extensions import db, login_manager
from models import Usuario
import routes.auth as auth_bp
import routes.dashboard as dashboard_bp
import routes.produtos as produtos_bp
import routes.movimentacoes as mov_bp
import routes.fornecedores as forn_bp

load_dotenv()

def _migrar_banco(app):
    """Adiciona colunas novas sem apagar dados existentes (migração manual para SQLite)."""
    with app.app_context():
        import sqlite3, os, secrets
        db_path = os.path.join(app.instance_path, 'estoquesmart.db')
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        migracoes = [
            ("produtos",      "preco_custo",     "NUMERIC(10,2)"),
            ("produtos",      "preco_venda",     "NUMERIC(10,2)"),
            ("movimentacoes", "preco_unitario",   "NUMERIC(10,2)"),
            ("usuarios",      "cargo",            "VARCHAR(20) NOT NULL DEFAULT 'funcionario'"),
        ]
        for tabela, coluna, tipo in migracoes:
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = [row[1] for row in cursor.fetchall()]
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
                print(f"[migração] Coluna '{coluna}' adicionada em '{tabela}'.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(150) NOT NULL,
                codigo_convite VARCHAR(20) NOT NULL UNIQUE,
                criado_em DATETIME
            )
        """)

        precisa_empresa_id = {}
        for tabela in ("usuarios", "produtos", "fornecedores"):
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = [row[1] for row in cursor.fetchall()]
            precisa_empresa_id[tabela] = "empresa_id" not in colunas

        if any(precisa_empresa_id.values()):
            cursor.execute("SELECT id FROM empresas ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            if row:
                empresa_padrao_id = row[0]
            else:
                codigo = secrets.token_hex(4).upper()
                cursor.execute(
                    "INSERT INTO empresas (nome, codigo_convite, criado_em) VALUES (?, ?, datetime('now'))",
                    ('Empresa Padrão', codigo)
                )
                empresa_padrao_id = cursor.lastrowid
                print(f"[migração] Empresa padrão criada (código de convite: {codigo}).")

            for tabela in ("usuarios", "produtos", "fornecedores"):
                if precisa_empresa_id[tabela]:
                    cursor.execute(
                        f"ALTER TABLE {tabela} ADD COLUMN empresa_id INTEGER NOT NULL DEFAULT {empresa_padrao_id}"
                    )
                    print(f"[migração] Coluna 'empresa_id' adicionada em '{tabela}'.")

        cursor.execute("PRAGMA foreign_keys=off")

        cursor.execute("PRAGMA table_info(produtos)")
        colunas_produtos = [row[1] for row in cursor.fetchall()]
        if "usuario_id" in colunas_produtos:
            cursor.execute("""
                CREATE TABLE produtos_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    fornecedor_id INTEGER,
                    nome VARCHAR(150) NOT NULL,
                    codigo VARCHAR(50) NOT NULL,
                    quantidade_atual INTEGER NOT NULL,
                    quantidade_minima INTEGER NOT NULL,
                    preco_custo NUMERIC(10,2),
                    preco_venda NUMERIC(10,2),
                    criado_em DATETIME,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id),
                    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
                )
            """)
            cursor.execute("""
                INSERT INTO produtos_novo
                    (id, empresa_id, fornecedor_id, nome, codigo, quantidade_atual,
                     quantidade_minima, preco_custo, preco_venda, criado_em)
                SELECT id, empresa_id, fornecedor_id, nome, codigo, quantidade_atual,
                       quantidade_minima, preco_custo, preco_venda, criado_em
                FROM produtos
            """)
            cursor.execute("DROP TABLE produtos")
            cursor.execute("ALTER TABLE produtos_novo RENAME TO produtos")
            print("[migração] Coluna legada 'usuario_id' removida de 'produtos'.")

        cursor.execute("PRAGMA table_info(fornecedores)")
        colunas_fornecedores = [row[1] for row in cursor.fetchall()]
        if "usuario_id" in colunas_fornecedores:
            cursor.execute("""
                CREATE TABLE fornecedores_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    nome VARCHAR(150) NOT NULL,
                    cnpj VARCHAR(20),
                    contato VARCHAR(100),
                    telefone VARCHAR(30),
                    email VARCHAR(150),
                    endereco VARCHAR(255),
                    observacao TEXT,
                    ativo BOOLEAN NOT NULL,
                    criado_em DATETIME,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                )
            """)
            cursor.execute("""
                INSERT INTO fornecedores_novo
                    (id, empresa_id, nome, cnpj, contato, telefone, email,
                     endereco, observacao, ativo, criado_em)
                SELECT id, empresa_id, nome, cnpj, contato, telefone, email,
                       endereco, observacao, ativo, criado_em
                FROM fornecedores
            """)
            cursor.execute("DROP TABLE fornecedores")
            cursor.execute("ALTER TABLE fornecedores_novo RENAME TO fornecedores")
            print("[migração] Coluna legada 'usuario_id' removida de 'fornecedores'.")

        cursor.execute("PRAGMA foreign_keys=on")

        conn.commit()
        conn.close()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-inseguro-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoquesmart.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar o sistema.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    @app.errorhandler(403)
    def acesso_negado(e):
        return render_template('403.html'), 403

    app.register_blueprint(auth_bp.bp)
    app.register_blueprint(dashboard_bp.bp)
    app.register_blueprint(produtos_bp.bp)
    app.register_blueprint(mov_bp.bp)
    app.register_blueprint(forn_bp.bp)

    _migrar_banco(app)
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
