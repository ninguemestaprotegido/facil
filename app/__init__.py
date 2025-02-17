import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicializando SQLAlchemy antes de criar o app
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')


     # 🔥 Corrigindo o erro: Definir uma SECRET_KEY para sessão funcionar
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "minha_chave_super_segura")



    # Configuração do Banco de Dados
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql://", 1)

    if not database_url:
        database_url = "sqlite:///app.db"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o banco de dados e migração
    db.init_app(app)
    Migrate(app, db)

    # Importação das rotas
    from app.routes import main
    from app.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')


    return app
