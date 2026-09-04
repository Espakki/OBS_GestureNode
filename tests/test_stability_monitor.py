"""Testes do GestureStabilityMonitor — o guarda contra disparo acidental.

Regra: a ação só é liberada quando a mão fica parada por `stability_min_frames` frames
consecutivos, com movimento médio abaixo de `motion_threshold` pixels.
"""

import pytest

from engine.gesture_engine import GestureStabilityMonitor

PARADA = [(100, 100)] * 21


def deslocada(dx):
    return [(100 + dx, 100)] * 21


@pytest.fixture
def monitor():
    return GestureStabilityMonitor(
        motion_threshold=4, stability_min_frames=3, check_velocity=True
    )


def test_primeiro_frame_nunca_e_estavel(monitor):
    """Sem frame anterior não há como medir movimento — precisa de uma baseline."""
    assert monitor.update(PARADA) is False


def test_precisa_de_frames_consecutivos_parados(monitor):
    monitor.update(PARADA)  # baseline

    assert monitor.update(PARADA) is False  # 1 frame parado
    assert monitor.update(PARADA) is False  # 2 frames
    assert monitor.update(PARADA) is True  # 3 frames -> atinge o mínimo


def test_movimento_grande_derruba_a_estabilidade(monitor):
    monitor.update(PARADA)
    for _ in range(3):
        monitor.update(PARADA)
    assert monitor.update(PARADA) is True

    # um solavanco bem acima do threshold zera a contagem
    assert monitor.update(deslocada(50)) is False


def test_contagem_reinicia_do_zero_apos_movimento(monitor):
    monitor.update(PARADA)
    monitor.update(deslocada(50))

    # tem de acumular os 3 frames de novo, não continuar de onde parou
    assert monitor.update(deslocada(50)) is False
    assert monitor.update(deslocada(50)) is False
    assert monitor.update(deslocada(50)) is True


def test_reset_limpa_o_estado(monitor):
    monitor.update(PARADA)
    for _ in range(4):
        monitor.update(PARADA)

    monitor.reset()

    assert monitor.previous_landmarks is None
    assert monitor.stable_frame_count == 0
    assert len(monitor.movement_history) == 0
    # após reset volta a precisar de baseline
    assert monitor.update(PARADA) is False


def test_movimento_abaixo_do_threshold_conta_como_parado(monitor):
    """Tremor natural da mão (< 4px) não deve impedir o disparo."""
    monitor.update(PARADA)
    assert monitor.update(deslocada(1)) is False
    assert monitor.update(PARADA) is False
    assert monitor.update(deslocada(1)) is True


class TestListasIncompativeis:
    def test_contagem_diferente_de_pontos_e_tratada_como_movimento_infinito(self, monitor):
        monitor.update(PARADA)
        assert monitor.update([(100, 100)] * 5) is False

    def test_lista_vazia_nao_estoura(self, monitor):
        monitor.update(PARADA)
        assert monitor.update([]) is False
