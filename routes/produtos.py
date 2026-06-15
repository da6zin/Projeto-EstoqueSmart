from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from extensions import db
from models import Produto, Fornecedor
from decimal import Decimal, InvalidOperation
from decorators import admin_required
import csv
import io

bp = Blueprint('produtos', __name__, url_prefix='/produtos')


def _get_fornecedores():
    return Fornecedor.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).order_by(Fornecedor.nome).all()


def _parse_preco(valor_str):
    if not valor_str or not valor_str.strip():
        return None
    try:
        return Decimal(valor_str.strip().replace(',', '.'))
    except InvalidOperation:
        return None


@bp.route('/')
@login_required
def listar():
    busca = request.args.get('q', '').strip()
    query = Produto.query.filter_by(empresa_id=current_user.empresa_id)

    if busca:
        query = query.filter(
            (Produto.nome.ilike(f'%{busca}%')) |
            (Produto.codigo.ilike(f'%{busca}%'))
        )

    produtos = query.order_by(Produto.nome).all()
    return render_template('produtos/listar.html', produtos=produtos, busca=busca)


@bp.route('/exportar')
@login_required
def exportar_csv():
    """Gera um arquivo CSV com todos os produtos da empresa, compatível com Excel."""
    busca = request.args.get('q', '').strip()
    query = Produto.query.filter_by(empresa_id=current_user.empresa_id)

    if busca:
        query = query.filter(
            (Produto.nome.ilike(f'%{busca}%')) |
            (Produto.codigo.ilike(f'%{busca}%'))
        )

    produtos = query.order_by(Produto.nome).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow([
        'Nome', 'Código', 'Fornecedor',
        'Quantidade Atual', 'Quantidade Mínima',
        'Preço de Custo', 'Status'
    ])

    for p in produtos:
        status = 'Estoque baixo' if p.quantidade_atual <= p.quantidade_minima else 'OK'
        preco = str(p.preco_custo).replace('.', ',') if p.preco_custo is not None else ''
        writer.writerow([
            p.nome,
            p.codigo,
            p.fornecedor.nome if p.fornecedor else '',
            p.quantidade_atual,
            p.quantidade_minima,
            preco,
            status,
        ])

    csv_data = output.getvalue()
    output.close()

    csv_bytes = '\ufeff' + csv_data

    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=produtos.csv'}
    )


@bp.route('/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo():
    fornecedores = _get_fornecedores()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        qtd_atual = request.form.get('quantidade_atual', '0')
        qtd_minima = request.form.get('quantidade_minima', '5')
        fornecedor_id = request.form.get('fornecedor_id') or None
        preco_custo = _parse_preco(request.form.get('preco_custo', ''))
        preco_venda = _parse_preco(request.form.get('preco_venda', ''))

        if not nome or not codigo:
            flash('Nome e código são obrigatórios.', 'danger')
            return render_template('produtos/form.html', produto=None, fornecedores=fornecedores)

        try:
            qtd_atual = int(qtd_atual)
            qtd_minima = int(qtd_minima)
        except ValueError:
            flash('Quantidades devem ser números inteiros.', 'danger')
            return render_template('produtos/form.html', produto=None, fornecedores=fornecedores)

        if qtd_atual < 0 or qtd_minima < 0:
            flash('Quantidades não podem ser negativas.', 'danger')
            return render_template('produtos/form.html', produto=None, fornecedores=fornecedores)

        produto = Produto(
            empresa_id=current_user.empresa_id,
            nome=nome,
            codigo=codigo,
            quantidade_atual=qtd_atual,
            quantidade_minima=qtd_minima,
            fornecedor_id=int(fornecedor_id) if fornecedor_id else None,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
        )
        db.session.add(produto)
        db.session.commit()

        flash(f'Produto "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))

    return render_template('produtos/form.html', produto=None, fornecedores=fornecedores)


@bp.route('/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(produto_id):
    produto = Produto.query.filter_by(id=produto_id, empresa_id=current_user.empresa_id).first_or_404()
    fornecedores = _get_fornecedores()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        qtd_minima = request.form.get('quantidade_minima', '5')
        fornecedor_id = request.form.get('fornecedor_id') or None
        preco_custo = _parse_preco(request.form.get('preco_custo', ''))
        preco_venda = _parse_preco(request.form.get('preco_venda', ''))

        if not nome or not codigo:
            flash('Nome e código são obrigatórios.', 'danger')
            return render_template('produtos/form.html', produto=produto, fornecedores=fornecedores)

        try:
            qtd_minima = int(qtd_minima)
        except ValueError:
            flash('Quantidade mínima deve ser um número inteiro.', 'danger')
            return render_template('produtos/form.html', produto=produto, fornecedores=fornecedores)

        if qtd_minima < 0:
            flash('Quantidade mínima não pode ser negativa.', 'danger')
            return render_template('produtos/form.html', produto=produto, fornecedores=fornecedores)

        produto.nome = nome
        produto.codigo = codigo
        produto.quantidade_minima = qtd_minima
        produto.fornecedor_id = int(fornecedor_id) if fornecedor_id else None
        produto.preco_custo = preco_custo
        produto.preco_venda = preco_venda
        db.session.commit()

        flash(f'Produto "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))

    return render_template('produtos/form.html', produto=produto, fornecedores=fornecedores)


@bp.route('/<int:produto_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir(produto_id):
    produto = Produto.query.filter_by(id=produto_id, empresa_id=current_user.empresa_id).first_or_404()
    nome = produto.nome
    db.session.delete(produto)
    db.session.commit()
    flash(f'Produto "{nome}" excluído.', 'info')
    return redirect(url_for('produtos.listar'))
