import os
from flask import Flask, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = 'your_secret_key_here'

    # Configuração do banco de dados
    database_url = os.getenv('DATABASE_URL')  # Obtém a URL do banco de dados
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    from app.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')

    @app.before_request
    def check_user_logged_in():
        open_endpoints = ['auth.login', 'auth.register']
        if 'user_id' not in session and request.endpoint not in open_endpoints:
            return redirect(url_for('auth.login'))

    # Aplicar as migrações automaticamente
    with app.app_context():
        try:
            from flask_migrate import upgrade
            upgrade()
            print("Migração aplicada com sucesso!")
        except OperationalError:
            print("Erro ao aplicar migração. Talvez o banco ainda não esteja pronto.")

    return app
