from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from models import Produto, Movimentacao
from datetime import datetime, timedelta, timezone

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    produtos = Produto.query.filter_by(empresa_id=current_user.empresa_id).all()
    criticos = [p for p in produtos if p.estoque_critico]

    agora_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio_hoje = agora_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_hoje = inicio_hoje + timedelta(days=1)

    movs_hoje = (
        Movimentacao.query
        .join(Produto)
        .filter(
            Produto.empresa_id == current_user.empresa_id,
            Movimentacao.criado_em >= inicio_hoje,
            Movimentacao.criado_em < fim_hoje,
        )
        .order_by(Movimentacao.criado_em.desc())
        .limit(20)
        .all()
    )

    receita_hoje = sum(
        float(m.preco_unitario) * m.quantidade
        for m in movs_hoje
        if m.tipo == 'saida' and m.preco_unitario is not None
    )
    custo_hoje = sum(
        float(m.preco_unitario) * m.quantidade
        for m in movs_hoje
        if m.tipo == 'entrada' and m.preco_unitario is not None
    )
    lucro_hoje = 0.0
    for m in movs_hoje:
        if m.tipo == 'saida' and m.preco_unitario is not None:
            custo_unit = float(m.produto.preco_custo) if m.produto.preco_custo else 0.0
            lucro_hoje += (float(m.preco_unitario) - custo_unit) * m.quantidade

    return render_template(
        'dashboard/index.html',
        total_produtos=len(produtos),
        total_criticos=len(criticos),
        produtos_criticos=criticos,
        movs_hoje=movs_hoje,
        receita_hoje=receita_hoje,
        lucro_hoje=lucro_hoje,
    )
