"""Garante que todo gesto que o detector produz chega à config com o nome certo.

Este é o teste que teria pego o bug original: existiam três cópias divergentes de
GESTURE_ALIASES, e uma mapeava "ROCK" -> "ROCK" enquanto a config usava "Rock". O
binding nunca casava e o gesto simplesmente não disparava, sem erro nenhum. Ver D-07.
"""

import pytest

from core.gesture_aliases import GESTURE_ALIASES
from core.gesture_detector import GestureDetector
from tests.maos_sinteticas import mao, mao_com
from tests.test_gesture_detector import GESTOS


def _nome_final(bruto):
    """Reproduz o que a engine faz: normaliza o retorno do detector."""
    return GESTURE_ALIASES.get(bruto, bruto)


# Nomes de exibição que a UI e a config usam. Fonte: aba Gestos / config.json.
NOMES_DE_EXIBICAO = {
    "V", "Joinha", "Mão aberta", "Punho", "Apontando p/ cima", "Rock", "Três",
    "Quatro", "OK", "Me liga", "Deslike", "Dedo do Meio", "Arminha", "Escoteiro",
}


@pytest.mark.parametrize("bruto,_forma", GESTOS, ids=[nome for nome, _ in GESTOS])
def test_todo_gesto_detectado_vira_nome_de_exibicao(bruto, _forma):
    """Nenhum código interno pode vazar para a config sem tradução."""
    assert _nome_final(bruto) in NOMES_DE_EXIBICAO


def test_escoteiro_e_ok_sign_tambem_traduzem():
    assert _nome_final("Escoteiro") in NOMES_DE_EXIBICAO
    assert _nome_final("OK_SIGN") in NOMES_DE_EXIBICAO


def test_detector_nao_produz_gesto_desconhecido():
    """Varre todas as formas possíveis de mão e confere que nada escapa do mapa.

    16 combinações de dedos x 4 estados de polegar. Se alguém adicionar um gesto novo
    ao detector e esquecer do alias, este teste quebra.
    """
    detector = GestureDetector()
    vistos = set()

    for indicador in (False, True):
        for medio in (False, True):
            for anelar in (False, True):
                for minimo in (False, True):
                    for polegar in ("fechado", "aberto_cima", "aberto_baixo", "aberto_lado"):
                        forma = mao(
                            indicador=indicador, medio=medio, anelar=anelar,
                            minimo=minimo, polegar=polegar,
                        )
                        bruto = detector.detectar(forma)
                        if bruto is not None:
                            vistos.add(bruto)

    assert vistos, "a varredura deveria produzir pelo menos um gesto"

    sem_traducao = {g for g in vistos if _nome_final(g) not in NOMES_DE_EXIBICAO}
    assert not sem_traducao, f"gestos sem nome de exibição: {sem_traducao}"


def test_valores_do_mapa_sao_todos_nomes_de_exibicao():
    """Nenhuma entrada do alias pode apontar para um nome que a UI não conhece."""
    desconhecidos = set(GESTURE_ALIASES.values()) - NOMES_DE_EXIBICAO
    assert not desconhecidos, f"aliases apontando para nomes inexistentes: {desconhecidos}"


def test_mapa_e_idempotente():
    """Normalizar duas vezes tem de dar o mesmo resultado.

    A engine chama _normalize_gesture_name em pontos diferentes; se um nome de exibição
    fosse também chave do mapa, a segunda passada mudaria o valor.
    """
    for valor in GESTURE_ALIASES.values():
        assert _nome_final(valor) == valor, f"{valor!r} muda ao ser normalizado de novo"
