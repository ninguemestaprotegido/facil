import re
from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

auth = Blueprint('auth', __name__)

# Função para validar senha forte
def is_password_strong(password):
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$', password))

# Rota de Registro
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validação da senha
        if not is_password_strong(password):
            return render_template('register.html', error="Senha fraca! Use pelo menos 8 caracteres, com letras e números.")

        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Usuário já existe! Escolha outro nome.")

        # Criar usuário e salvar no banco
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Rota de Login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Verificação de credenciais
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error="Usuário ou senha incorretos!")

        # Armazena o usuário na sessão
        session['user_id'] = user.id
        return redirect(url_for('main.home'))

    return render_template('login.html')

# Rota de Logout
@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))

@auth.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('main.home'))  # Redireciona para a página principal após a exclusão

