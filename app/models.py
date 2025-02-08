from . import db
from sqlalchemy.orm import relationship

class Colaborador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    # Relacionamento com Importacao com cascata para exclusão
    importacoes = relationship('Importacao', backref='colaborador', cascade='all, delete-orphan')

class Importacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('colaborador.id'), nullable=False)
    refile = db.Column(db.Float, nullable=False)
