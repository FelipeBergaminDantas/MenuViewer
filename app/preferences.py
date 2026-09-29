"""Preferências de acessibilidade do visitante.

Ficam em um único cookie (formato de query string: `fonte=1.2&contraste=1`),
lido pelo servidor a cada requisição. Isso permite:

- renderizar a página já no estado certo (sem "piscar" ao carregar);
- funcionar sem JavaScript (os controles são formulários comuns);
- testar o comportamento no servidor com pytest.

O JavaScript (`static/js/preferencias.js`) escreve o mesmo cookie para aplicar
mudanças visuais na hora, sem recarregar a página.
"""

from dataclasses import asdict, dataclass, replace
from urllib.parse import parse_qs, urlencode

FONTE_MIN = 0.8
FONTE_MAX = 2.0
FONTE_PASSO = 0.1

BOOLEANOS = ("contraste", "movimento_reduzido", "simplificado", "voz_falada")


@dataclass(frozen=True)
class Preferencias:
    fonte: float = 1.0
    contraste: bool = False
    movimento_reduzido: bool = False
    simplificado: bool = False
    voz_falada: bool = True  # respostas faladas dos comandos de voz
    idioma: str = ""  # vazio = detectar pelo navegador

    @classmethod
    def from_cookie(cls, valor, idiomas):
        """Lê o cookie de forma tolerante: valores inválidos voltam ao padrão."""
        if not valor:
            return cls()
        try:
            dados = {k: v[-1] for k, v in parse_qs(valor, keep_blank_values=True).items()}
        except (TypeError, ValueError):
            return cls()

        padrao = cls()
        kwargs = {}
        try:
            kwargs["fonte"] = limitar_fonte(float(dados.get("fonte", padrao.fonte)))
        except ValueError:
            pass
        for chave in BOOLEANOS:
            if chave in dados:
                kwargs[chave] = dados[chave] == "1"
        if dados.get("idioma") in idiomas:
            kwargs["idioma"] = dados["idioma"]
        return cls(**kwargs)

    def to_cookie(self):
        dados = asdict(self)
        dados["fonte"] = f"{self.fonte:.2f}"
        for chave in BOOLEANOS:
            dados[chave] = "1" if dados[chave] else "0"
        return urlencode(dados)

    def aplicar(self, acao, valor=None, idiomas=()):
        """Retorna uma nova instância com a ação do formulário aplicada."""
        if acao == "fonte_mais":
            return replace(self, fonte=limitar_fonte(self.fonte + FONTE_PASSO))
        if acao == "fonte_menos":
            return replace(self, fonte=limitar_fonte(self.fonte - FONTE_PASSO))
        if acao == "fonte_padrao":
            return replace(self, fonte=1.0)
        if acao in BOOLEANOS:
            return replace(self, **{acao: not getattr(self, acao)})
        if acao == "idioma" and valor in idiomas:
            return replace(self, idioma=valor)
        return self

    @property
    def fonte_percentual(self):
        return round(self.fonte * 100)

    @property
    def classes_html(self):
        """Classes aplicadas em <html> para o CSS reagir às preferências."""
        classes = []
        if self.contraste:
            classes.append("alto-contraste")
        if self.movimento_reduzido:
            classes.append("movimento-reduzido")
        if self.simplificado:
            classes.append("modo-simplificado")
        return " ".join(classes)


def limitar_fonte(valor):
    return round(min(FONTE_MAX, max(FONTE_MIN, valor)), 2)
