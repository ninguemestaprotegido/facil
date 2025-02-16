from app import db  # Import db from __init__.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Colaborador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    importacoes = db.relationship('Importacao', backref='colaborador', cascade='all, delete-orphan')

class Importacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('colaborador.id'), nullable=False)
    refile = db.Column(db.Float, nullable=False)
