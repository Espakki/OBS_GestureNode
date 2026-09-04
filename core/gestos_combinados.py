"""Chave canônica de um gesto combinado — o par de mãos tratado como uma unidade.

Mesmo padrão de `gesture_aliases.py` e `modos.py`: módulo pequeno, sem dependências,
importado por engine e UI para que não existam duas formas de montar a mesma chave.

O par é **não ordenado** (D-30): "V + Joinha" e "Joinha + V" são o mesmo combinado. Isso
segue o D-03, que já definiu que a identidade da mão não importa para bindings individuais
— um Joinha aciona a mesma ação vindo da esquerda ou da direita. Seria incoerente o
combinado passar a distinguir mãos quando o individual não distingue.
"""

SEPARADOR = " + "


def chave_do_par(gesto_a, gesto_b):
    """Monta a chave canônica de um par, independente da ordem em que veio.

    Ordena alfabeticamente, então `chave_do_par("V", "Joinha")` e
    `chave_do_par("Joinha", "V")` devolvem a mesma string.
    """
    return SEPARADOR.join(sorted([gesto_a, gesto_b]))


def par_da_chave(chave):
    """Volta de `"Joinha + V"` para `("Joinha", "V")`.

    Devolve `None` se a chave não tiver exatamente dois gestos — protege contra entrada
    corrompida no config, que de outro jeito viraria unpacking com erro em runtime.
    """
    partes = str(chave).split(SEPARADOR)
    if len(partes) != 2 or not all(p.strip() for p in partes):
        return None
    return (partes[0], partes[1])


def e_chave_de_par(chave):
    """True se a string tem forma de chave de par. Usado para rotear a UI."""
    return par_da_chave(chave) is not None
