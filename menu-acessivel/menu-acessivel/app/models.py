from app.database import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    ordem = db.Column(db.Integer, default=0)

    pratos = db.relationship("Prato", backref="categoria", lazy=True)

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class Prato(db.Model):
    __tablename__ = "pratos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False, default="")
    preco = db.Column(db.Float, nullable=False, default=0.0)
    imagem = db.Column(db.String(200), nullable=True)  # nome do arquivo em static/img/pratos
    imagem_alt = db.Column(db.String(300), nullable=True)  # texto alternativo descritivo

    vegano = db.Column(db.Boolean, default=False)
    sem_gluten = db.Column(db.Boolean, default=False)
    picante = db.Column(db.Boolean, default=False)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)

    def __repr__(self):
        return f"<Prato {self.nome}>"
