"""Internacionalização da interface, feita no servidor.

As traduções ficam em `app/translations/<idioma>.json` (JSON aninhado, acessado
por chaves com ponto: `filtros.titulo`). Texto traduzido já vem no HTML, então
leitores de tela e buscadores recebem o idioma correto desde o primeiro carregamento.

Para adicionar um idioma: crie o JSON, inclua o código em `Config.IDIOMAS` e em
`METADADOS` abaixo.
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import current_app, g, request

PASTA = Path(__file__).parent / "translations"

# código interno -> (atributo lang do HTML, idioma do reconhecimento de voz, nome nativo)
METADADOS = {
    "pt": ("pt-BR", "pt-BR", "Português"),
    "en": ("en", "en-US", "English"),
    "es": ("es", "es-ES", "Español"),
}


@lru_cache(maxsize=None)
def carregar(idioma):
    with open(PASTA / f"{idioma}.json", encoding="utf-8") as arquivo:
        return _achatar(json.load(arquivo))


def _achatar(dados, prefixo=""):
    plano = {}
    for chave, valor in dados.items():
        completa = f"{prefixo}{chave}"
        if isinstance(valor, dict):
            plano.update(_achatar(valor, f"{completa}."))
        else:
            plano[completa] = valor
    return plano


def idioma_padrao():
    return current_app.config["IDIOMAS"][0]


def resolver_idioma(preferido):
    idiomas = current_app.config["IDIOMAS"]
    if preferido in idiomas:
        return preferido
    return request.accept_languages.best_match(idiomas) or idioma_padrao()


def traduzir(chave, idioma=None, **variaveis):
    """Traduz `chave`; cai para o idioma padrão e, por fim, para a própria chave."""
    idioma = idioma or getattr(g, "idioma", None) or idioma_padrao()
    texto = carregar(idioma).get(chave)
    if texto is None:
        texto = carregar(idioma_padrao()).get(chave, chave)
    if variaveis and isinstance(texto, str):
        texto = texto.format(**variaveis)
    return texto


def traduzir_plural(chave, quantidade, **variaveis):
    """Usa `<chave>.um` para 1 e `<chave>.outros` para os demais."""
    sufixo = "um" if quantidade == 1 else "outros"
    return traduzir(f"{chave}.{sufixo}", n=quantidade, **variaveis)


def traduzir_secao(prefixo, idioma=None):
    """Todas as chaves sob `prefixo`, como dicionário (útil para enviar ao JS)."""
    idioma = idioma or getattr(g, "idioma", None) or idioma_padrao()
    base = {**carregar(idioma_padrao()), **carregar(idioma)}
    inicio = f"{prefixo}."
    return {chave[len(inicio):]: valor for chave, valor in base.items() if chave.startswith(inicio)}
