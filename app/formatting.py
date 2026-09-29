"""Formatação de valores para exibição."""

from decimal import Decimal


def formatar_moeda(valor, idioma):
    """Formata um valor em reais conforme o idioma da interface.

    O cardápio é sempre cobrado em BRL; só a notação muda.
    >>> formatar_moeda(Decimal("1234.5"), "pt")
    'R$ 1.234,50'
    >>> formatar_moeda(Decimal("1234.5"), "en")
    'R$1,234.50'
    """
    texto = f"{Decimal(valor):,.2f}"  # 1,234.50
    if idioma == "en":
        return f"R${texto}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"
