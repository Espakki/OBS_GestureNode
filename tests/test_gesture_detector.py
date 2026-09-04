"""Testes do GestureDetector com landmarks sintéticos — sem webcam, sem MediaPipe."""

import pytest

from core.gesture_detector import GestureDetector
from tests.maos_sinteticas import mao, mao_com


@pytest.fixture
def detector():
    return GestureDetector()


# (nome esperado, kwargs para montar a mão)
GESTOS = [
    ("THUMBS_UP", dict(polegar="aberto_cima")),
    ("THUMBS_DOWN", dict(polegar="aberto_baixo")),
    ("FIST", dict(polegar="fechado")),
    ("OPEN_HAND", dict(indicador=True, medio=True, anelar=True, minimo=True, polegar="aberto_lado")),
    ("FOUR", dict(indicador=True, medio=True, anelar=True, minimo=True, polegar="fechado")),
    ("THREE", dict(indicador=True, medio=True, anelar=True, polegar="fechado")),
    ("V", dict(indicador=True, medio=True, polegar="fechado")),
    ("ROCK", dict(indicador=True, minimo=True, polegar="fechado")),
    ("CALL_ME", dict(minimo=True, polegar="aberto_lado")),
    ("Dedo do Meio", dict(medio=True, polegar="fechado")),
    ("POINT", dict(indicador=True, polegar="fechado")),
    ("Arminha", dict(indicador=True, polegar="aberto_lado")),
]


@pytest.mark.parametrize("esperado,forma", GESTOS, ids=[nome for nome, _ in GESTOS])
def test_detecta_cada_gesto(detector, esperado, forma):
    assert detector.detectar(mao(**forma)) == esperado


def test_escoteiro_quando_pontas_se_tocam(detector):
    """Escoteiro é um V com indicador e médio encostados (dist < palm_size * 0.25)."""
    v = mao(indicador=True, medio=True, polegar="fechado")
    assert detector.detectar(v) == "V"

    escoteiro = mao_com(v, {8: (85, 255)})
    assert detector.detectar(escoteiro) == "Escoteiro"


def test_ok_sign_com_polegar_encostando_no_indicador(detector):
    """OK exige indicador dobrado, polegar colado nele e os outros três estendidos."""
    base = mao(medio=True, anelar=True, minimo=True, polegar="fechado")
    ok = mao_com(base, {4: (95, 355)})
    assert detector.detectar(ok) == "OK_SIGN"


class TestEntradaInvalida:
    def test_lista_vazia_retorna_none(self, detector):
        assert detector.detectar([]) is None

    def test_menos_de_21_pontos_retorna_none(self, detector):
        assert detector.detectar([(0, 0)] * 20) is None

    def test_mais_de_21_pontos_retorna_none(self, detector):
        """Duas mãos concatenadas (42 pontos) devem ser rejeitadas, não interpretadas.

        Guarda o pitfall CRITICAL-01: antes da API multi-mão, habilitar 2 mãos fazia
        `processar()` devolver uma lista achatada de 42 pontos e a detecção morria em
        silêncio.
        """
        assert detector.detectar([(0, 0)] * 42) is None


class TestFronteirasFrageis:
    """Pares que diferem por um único booleano — documentam onde a detecção é sensível.

    Se alguém mexer nos limiares do detector, estes testes dizem qual par quebrou.
    """

    def test_arminha_e_point_diferem_so_pelo_polegar(self, detector):
        assert detector.detectar(mao(indicador=True, polegar="fechado")) == "POINT"
        assert detector.detectar(mao(indicador=True, polegar="aberto_lado")) == "Arminha"

    def test_open_hand_e_four_diferem_so_pelo_polegar(self, detector):
        quatro_dedos = dict(indicador=True, medio=True, anelar=True, minimo=True)
        assert detector.detectar(mao(**quatro_dedos, polegar="fechado")) == "FOUR"
        assert detector.detectar(mao(**quatro_dedos, polegar="aberto_lado")) == "OPEN_HAND"

    def test_thumbs_up_e_down_diferem_so_pela_altura_da_ponta(self, detector):
        assert detector.detectar(mao(polegar="aberto_cima")) == "THUMBS_UP"
        assert detector.detectar(mao(polegar="aberto_baixo")) == "THUMBS_DOWN"

    def test_mao_fechada_com_polegar_aberto_de_lado_nao_dispara_nada(self, detector):
        """Pose ambígua devolve None — nem joinha, nem deslike, nem punho.

        FIST exige `not thumb_open`, e THUMBS_UP/DOWN exigem que a ponta do polegar
        esteja claramente acima ou abaixo. Com o polegar aberto na horizontal nenhum
        dos três casa, e o detector prefere não classificar a chutar.

        Comportamento correto para um app de live: um gesto ambíguo não deve trocar
        a cena. Se algum dia isso virar FIST, foi mudança deliberada — não deixe
        acontecer por acidente.
        """
        assert detector.detectar(mao(polegar="aberto_lado")) is None

    def test_punho_exige_polegar_recolhido(self, detector):
        assert detector.detectar(mao(polegar="fechado")) == "FIST"


class TestLimiarDeDedoEstendido:
    """Fixa o limiar `dist_tip > dist_mcp * 1.2` de `_finger_extended`.

    Os outros testes usam poses extremas (ponta a ~150px do pulso quando estendida,
    ~57px quando dobrada) e passariam com quase qualquer limiar. Estes exercitam a
    fronteira: a base do indicador está a ~95px do pulso, então o corte fica em ~114px.
    """

    # ~105px do pulso: acima de 1.05x (~100px), abaixo de 1.2x (~114px)
    PONTA_AMBIGUA = (67, 300)
    # ~123px do pulso: acima de 1.2x
    PONTA_ESTENDIDA = (70, 280)

    def test_dedo_meio_esticado_ainda_conta_como_dobrado(self, detector):
        """Um indicador parcialmente esticado não vira POINT.

        Se este teste virar POINT, o limiar foi afrouxado — e gestos vão disparar com
        a mão relaxada, que é justamente o que o hold_time e o stability monitor
        tentam evitar.
        """
        forma = mao_com(mao(polegar="fechado"), {8: self.PONTA_AMBIGUA})
        assert detector.detectar(forma) == "FIST"

    def test_dedo_claramente_esticado_conta_como_estendido(self, detector):
        forma = mao_com(mao(polegar="fechado"), {8: self.PONTA_ESTENDIDA})
        assert detector.detectar(forma) == "POINT"
