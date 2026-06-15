from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Fornecedor
from decorators import admin_required

bp = Blueprint('fornecedores', __name__, url_prefix='/fornecedores')


@bp.route('/')
@login_required
def listar():
    busca = request.args.get('q', '').strip()
    apenas_ativos = request.args.get('ativos', '1')

    query = Fornecedor.query.filter_by(empresa_id=current_user.empresa_id)

    if apenas_ativos == '1':
        query = query.filter_by(ativo=True)

    if busca:
        query = query.filter(
            (Fornecedor.nome.ilike(f'%{busca}%')) |
            (Fornecedor.cnpj.ilike(f'%{busca}%')) |
            (Fornecedor.contato.ilike(f'%{busca}%'))
        )

    fornecedores = query.order_by(Fornecedor.nome).all()
    return render_template('fornecedores/listar.html',
                           fornecedores=fornecedores,
                           busca=busca,
                           apenas_ativos=apenas_ativos)


@bp.route('/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Nome do fornecedor é obrigatório.', 'danger')
            return render_template('fornecedores/form.html', fornecedor=None)

        fornecedor = Fornecedor(
            empresa_id=current_user.empresa_id,
            nome=nome,
            cnpj=request.form.get('cnpj', '').strip() or None,
            contato=request.form.get('contato', '').strip() or None,
            telefone=request.form.get('telefone', '').strip() or None,
            email=request.form.get('email', '').strip() or None,
            endereco=request.form.get('endereco', '').strip() or None,
            observacao=request.form.get('observacao', '').strip() or None,
        )
        db.session.add(fornecedor)
        db.session.commit()
        flash(f'Fornecedor "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('fornecedores.listar'))

    return render_template('fornecedores/form.html', fornecedor=None)


@bp.route('/<int:fornecedor_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(fornecedor_id):
    fornecedor = Fornecedor.query.filter_by(
        id=fornecedor_id, empresa_id=current_user.empresa_id
    ).first_or_404()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Nome do fornecedor é obrigatório.', 'danger')
            return render_template('fornecedores/form.html', fornecedor=fornecedor)

        fornecedor.nome = nome
        fornecedor.cnpj = request.form.get('cnpj', '').strip() or None
        fornecedor.contato = request.form.get('contato', '').strip() or None
        fornecedor.telefone = request.form.get('telefone', '').strip() or None
        fornecedor.email = request.form.get('email', '').strip() or None
        fornecedor.endereco = request.form.get('endereco', '').strip() or None
        fornecedor.observacao = request.form.get('observacao', '').strip() or None
        db.session.commit()

        flash(f'Fornecedor "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('fornecedores.listar'))

    return render_template('fornecedores/form.html', fornecedor=fornecedor)


@bp.route('/<int:fornecedor_id>/toggle-ativo', methods=['POST'])
@login_required
@admin_required
def toggle_ativo(fornecedor_id):
    fornecedor = Fornecedor.query.filter_by(
        id=fornecedor_id, empresa_id=current_user.empresa_id
    ).first_or_404()
    fornecedor.ativo = not fornecedor.ativo
    db.session.commit()
    status = 'ativado' if fornecedor.ativo else 'desativado'
    flash(f'Fornecedor "{fornecedor.nome}" {status}.', 'info')
    return redirect(url_for('fornecedores.listar'))


@bp.route('/<int:fornecedor_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir(fornecedor_id):
    fornecedor = Fornecedor.query.filter_by(
        id=fornecedor_id, empresa_id=current_user.empresa_id
    ).first_or_404()
    for p in fornecedor.produtos:
        p.fornecedor_id = None
    nome = fornecedor.nome
    db.session.delete(fornecedor)
    db.session.commit()
    flash(f'Fornecedor "{nome}" excluído.', 'info')
    return redirect(url_for('fornecedores.listar'))
