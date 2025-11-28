from app import db

class Local(db.Model):
    __tablename__ = 'locais'
    __table_args__ = {'schema': 'inventario_2025'}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    estante = db.Column(db.String(150), nullable=False)
    pecas = db.relationship('Peca', backref='local', lazy=True, cascade='all, delete-orphan')
    almoxarifado = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Local {self.nome} do {self.almoxarifado}>'

class Peca(db.Model):
    __tablename__ = 'pecas'
    __table_args__ = {'schema': 'inventario_2025'}

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    local_id = db.Column(db.Integer, db.ForeignKey('inventario_2025.locais.id'), nullable=False) 
    quantidade = db.relationship('Quantidade', backref='peca', lazy=True, cascade='all, delete-orphan')
    quantidade_sistema = db.Column(db.Float, nullable=True)
    peca_fora_lista = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Peça {self.codigo}, Quantidade {self.quantidade.quantidade if self.quantidade else "não definida"}, Quantidade no sistema {self.quantidade_sistema}>'

class Quantidade(db.Model):
    __tablename__ = 'quantidades'
    __table_args__ = {'schema': 'inventario_2025'}

    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Float, nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey('inventario_2025.pecas.id'), nullable=False)  # Chave estrangeira para Peca

    def __repr__(self):
        return f'<Quantidade {self.quantidade}>'
