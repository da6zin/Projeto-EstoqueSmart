from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Usuario, Empresa
import secrets

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        nome      = request.form.get('nome', '').strip()
        email     = request.form.get('email', '').strip().lower()
        senha     = request.form.get('senha', '')
        confirmar = request.form.get('confirmar', '')
        cargo     = request.form.get('cargo', 'funcionario')
        codigo_convite = request.form.get('codigo_convite', '').strip().upper()

        if not nome or not email or not senha:
            flash('Preencha todos os campos.', 'danger')
            return render_template('auth/cadastro.html')

        if senha != confirmar:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/cadastro.html')

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/cadastro.html')

        if cargo not in ('admin', 'funcionario'):
            cargo = 'funcionario'

        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
            return render_template('auth/cadastro.html')

        if cargo == 'admin':
            empresa = Empresa(
                nome=request.form.get('nome_empresa', '').strip() or f'{nome} - Empresa',
                codigo_convite=secrets.token_hex(4).upper()
            )
            db.session.add(empresa)
            db.session.flush()
        else:
            empresa = Empresa.query.filter_by(codigo_convite=codigo_convite).first()
            if not empresa:
                flash('Código de convite inválido.', 'danger')
                return render_template('auth/cadastro.html')

        usuario = Usuario(
            empresa_id=empresa.id,
            nome=nome,
            email=email,
            cargo=cargo
        )
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()

        if cargo == 'admin':
            flash(f'Conta criada! Código da sua empresa: {empresa.codigo_convite} — compartilhe com seus funcionários.', 'success')
        else:
            flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/cadastro.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.checar_senha(senha):
            login_user(usuario, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))

        flash('E-mail ou senha incorretos.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))
