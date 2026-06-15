from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Produto, Movimentacao
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal, InvalidOperation

bp = Blueprint('movimentacoes', __name__, url_prefix='/movimentacoes')


def _parse_preco(valor_str):
    """Converte string de preço para Decimal ou None."""
    if not valor_str or not valor_str.strip():
        return None
    try:
        return Decimal(valor_str.strip().replace(',', '.'))
    except InvalidOperation:
        return None


def _processar_movimentacao(produto, tipo, quantidade_str, preco_str, observacao, template, template_kwargs):
    if tipo not in ('entrada', 'saida'):
        flash('Tipo de movimentação inválido.', 'danger')
        return render_template(template, **template_kwargs)

    try:
        quantidade = int(quantidade_str)
    except (ValueError, TypeError):
        flash('Quantidade deve ser um número inteiro.', 'danger')
        return render_template(template, **template_kwargs)

    if quantidade <= 0:
        flash('Quantidade deve ser maior que zero.', 'danger')
        return render_template(template, **template_kwargs)

    if tipo == 'saida' and quantidade > produto.quantidade_atual:
        flash(
            f'Estoque insuficiente. Disponível: {produto.quantidade_atual} unidade(s).',
            'danger'
        )
        return render_template(template, **template_kwargs)

    preco = _parse_preco(preco_str)

    if tipo == 'entrada':
        produto.quantidade_atual += quantidade
        if preco is not None:
            produto.preco_custo = preco
    else:
        produto.quantidade_atual -= quantidade

    mov = Movimentacao(
        produto_id=produto.id,
        tipo=tipo,
        quantidade=quantidade,
        preco_unitario=preco,
        observacao=observacao or None,
    )
    db.session.add(mov)
    db.session.commit()

    label = 'Entrada' if tipo == 'entrada' else 'Saída'
    flash(f'{label} de {quantidade} unidade(s) registrada para "{produto.nome}".', 'success')
    return None


@bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_geral():
    produtos = Produto.query.filter_by(empresa_id=current_user.empresa_id).order_by(Produto.nome).all()

    produto_selecionado = None
    produto_id_qs = request.args.get('produto_id')
    if produto_id_qs:
        try:
            produto_selecionado = Produto.query.filter_by(
                id=int(produto_id_qs), empresa_id=current_user.empresa_id
            ).first()
        except ValueError:
            pass

    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        try:
            produto = Produto.query.filter_by(
                id=int(produto_id), empresa_id=current_user.empresa_id
            ).first_or_404()
        except (ValueError, TypeError):
            flash('Produto inválido.', 'danger')
            return render_template('movimentacoes/form_geral.html',
                                   produtos=produtos, produto_selecionado=None)

        tipo = request.form.get('tipo')
        quantidade_str = request.form.get('quantidade', '0')
        preco_str = request.form.get('preco_unitario', '')
        observacao = request.form.get('observacao', '').strip()

        kwargs = dict(produtos=produtos, produto_selecionado=produto)
        erro = _processar_movimentacao(produto, tipo, quantidade_str, preco_str, observacao,
                                       'movimentacoes/form_geral.html', kwargs)
        if erro:
            return erro
        return redirect(url_for('dashboard.index'))

    return render_template('movimentacoes/form_geral.html',
                           produtos=produtos, produto_selecionado=produto_selecionado)


@bp.route('/registrar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def registrar(produto_id):
    produto = Produto.query.filter_by(id=produto_id, empresa_id=current_user.empresa_id).first_or_404()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        quantidade_str = request.form.get('quantidade', '0')
        preco_str = request.form.get('preco_unitario', '')
        observacao = request.form.get('observacao', '').strip()

        kwargs = dict(produto=produto)
        erro = _processar_movimentacao(produto, tipo, quantidade_str, preco_str, observacao,
                                       'movimentacoes/form.html', kwargs)
        if erro:
            return erro
        return redirect(url_for('dashboard.index'))

    return render_template('movimentacoes/form.html', produto=produto)


@bp.route('/historico')
@login_required
def historico():
    data_str = request.args.get('data', '')
    produto_id = request.args.get('produto_id', '')

    query = (
        Movimentacao.query
        .join(Produto)
        .filter(Produto.empresa_id == current_user.empresa_id)
    )

    if data_str:
        try:
            data_filtro = date.fromisoformat(data_str)
            inicio = datetime.combine(data_filtro, datetime.min.time())
            fim = inicio + timedelta(days=1)
            query = query.filter(
                Movimentacao.criado_em >= inicio,
                Movimentacao.criado_em < fim,
            )
        except ValueError:
            pass

    if produto_id:
        try:
            query = query.filter(Movimentacao.produto_id == int(produto_id))
        except ValueError:
            pass

    movimentacoes = query.order_by(Movimentacao.criado_em.desc()).limit(100).all()
    produtos = Produto.query.filter_by(empresa_id=current_user.empresa_id).order_by(Produto.nome).all()

    return render_template(
        'movimentacoes/historico.html',
        movimentacoes=movimentacoes,
        produtos=produtos,
        data_filtro=data_str,
        produto_id_filtro=produto_id,
    )
