"""Modelo de dados do cardápio.

Alérgenos e restrições alimentares são *derivados dos ingredientes*, e não
marcados à mão em cada prato. Assim, cadastrar um ingrediente corretamente
uma vez garante que todo prato que o usa seja filtrado corretamente — e não
existe o risco de um prato marcado como "sem glúten" conter pão.
"""

import enum

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Origem(enum.Enum):
    """Origem de um ingrediente, usada para derivar dietas."""

    VEGETAL = "vegetal"  # compatível com dieta vegana
    ANIMAL = "animal"  # derivado animal sem carne (leite, ovo, mel): vegetariano
    CARNE = "carne"  # carne, aves, peixes e frutos do mar


prato_ingrediente = db.Table(
    "prato_ingrediente",
    db.Column("prato_id", db.ForeignKey("pratos.id", ondelete="CASCADE"), primary_key=True),
    db.Column("ingrediente_id", db.ForeignKey("ingredientes.id", ondelete="CASCADE"), primary_key=True),
)

ingrediente_alergeno = db.Table(
    "ingrediente_alergeno",
    db.Column("ingrediente_id", db.ForeignKey("ingredientes.id", ondelete="CASCADE"), primary_key=True),
    db.Column("alergeno_id", db.ForeignKey("alergenos.id", ondelete="CASCADE"), primary_key=True),
)


class Alergeno(db.Model):
    """Alérgeno alimentar. O nome exibido vem das traduções (`alergeno.<codigo>`)."""

    __tablename__ = "alergenos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), nullable=False, unique=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Alergeno {self.codigo}>"


class Ingrediente(db.Model):
    __tablename__ = "ingredientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    origem = db.Column(db.Enum(Origem), nullable=False, default=Origem.VEGETAL)

    alergenos = db.relationship(
        "Alergeno", secondary=ingrediente_alergeno, lazy="selectin", order_by="Alergeno.ordem"
    )
    # Lado inverso de `Prato.ingredientes`. Faz o SQLAlchemy apagar as linhas de
    # `prato_ingrediente` ao excluir um ingrediente (o SQLite ignora ON DELETE
    # CASCADE sem `PRAGMA foreign_keys`).
    pratos = db.relationship(
        "Prato", secondary=prato_ingrediente, back_populates="ingredientes", order_by="Prato.nome"
    )

    def __repr__(self):
        return f"<Ingrediente {self.nome}>"


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    pratos = db.relationship("Prato", back_populates="categoria", order_by="Prato.ordem")

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class Prato(db.Model):
    __tablename__ = "pratos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False, default="")
    # Numeric evita erros de arredondamento de ponto flutuante em valores monetários.
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    imagem = db.Column(db.String(200))  # nome do arquivo em static/img/pratos
    imagem_alt = db.Column(db.String(300))  # texto alternativo descritivo
    picante = db.Column(db.Boolean, nullable=False, default=False)
    disponivel = db.Column(db.Boolean, nullable=False, default=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False, index=True)
    categoria = db.relationship("Categoria", back_populates="pratos")

    ingredientes = db.relationship(
        "Ingrediente",
        secondary=prato_ingrediente,
        back_populates="pratos",
        lazy="selectin",
        order_by="Ingrediente.nome",
    )

    @property
    def alergenos(self):
        """Alérgenos presentes no prato, sem repetição, na ordem de exibição."""
        vistos = {}
        for ingrediente in self.ingredientes:
            for alergeno in ingrediente.alergenos:
                vistos.setdefault(alergeno.id, alergeno)
        return sorted(vistos.values(), key=lambda a: a.ordem)

    @property
    def vegano(self):
        return bool(self.ingredientes) and all(i.origem is Origem.VEGETAL for i in self.ingredientes)

    @property
    def vegetariano(self):
        return bool(self.ingredientes) and all(i.origem is not Origem.CARNE for i in self.ingredientes)

    def __repr__(self):
        return f"<Prato {self.nome}>"


class Usuario(db.Model):
    """Pessoa da equipe com acesso ao painel admin (criada com `flask criar-admin`)."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), nullable=False, unique=True)
    senha_hash = db.Column(db.String(256), nullable=False)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.login}>"
