"""Duas mãos rastreadas, uma ação só: a primeira mão a fazer o gesto vence. Ver D-31.

Duas mãos existem para que ter as duas em quadro não atrapalhe — o usuário não precisa
esconder uma nem se preocupar com qual é a "mão certa". Mas a ação continua sendo de uma
mão só.
"""

import pytest

from engine.gesture_engine import GestureEngine


def engine_de_teste(bindings=None):
    """Engine em modo teste: registra disparos sem tocar em OBS, som ou atalho."""
    cfg = {
        "modo": "teste",
        "max_maos": 2,
        "camera": {"index": 0, "device_name": ""},
        "gestures": {
            "bindings": bindings or {},
            "default_hold_time": 1.0,
            "default_cooldown": 1.0,
        },
    }
    return GestureEngine(cfg)


def binding(hold_time=1.0, cooldown=1.0, enabled=True):
    return {
        "enabled": enabled,
        "hold_time": hold_time,
        "cooldown": cooldown,
        "scene": "",
        "sound_file": "",
        "hotkey": "",
        "use_scene": False,
        "use_sound": False,
        "use_hotkey": False,
    }


@pytest.fixture
def engine():
    e = engine_de_teste(
        bindings={"V": binding(), "Joinha": binding(), "Punho": binding()}
    )
    yield e
    e.action_executor.shutdown(wait=False)


# (gesto, estavel, inicio_do_hold)
def mao(gesto, estavel=True, inicio=100.0):
    return (gesto, estavel, inicio)


class TestUmaAcaoPorVez:
    def test_duas_maos_gestos_diferentes_disparam_uma_so(self, engine):
        """O caso que motivou a regra.

        Com as duas mãos em quadro fazendo gestos diferentes, disparar as duas ações
        trocaria duas cenas de uma vez — quase nunca o que se quer numa live.
        """
        maos = {
            "Left": mao("V", inicio=100.0),
            "Right": mao("Joinha", inicio=105.0),
        }
        disparos = {}
        engine._despachar_primeira_mao(maos, 110.0, disparos)

        assert len(disparos) == 1

    def test_vence_quem_comecou_o_gesto_primeiro(self, engine):
        maos = {
            "Left": mao("V", inicio=105.0),
            "Right": mao("Joinha", inicio=100.0),  # começou antes
        }
        disparos = {}
        engine._despachar_primeira_mao(maos, 110.0, disparos)

        assert set(disparos) == {"Joinha"}

    def test_criterio_nao_depende_da_ordem_das_maos(self, engine):
        """O MediaPipe não garante ordem. O desempate é pelo tempo, não pela posição."""
        a = {"Left": mao("V", inicio=105.0), "Right": mao("Joinha", inicio=100.0)}
        b = {"Right": mao("Joinha", inicio=100.0), "Left": mao("V", inicio=105.0)}

        d_a, d_b = {}, {}
        engine._despachar_primeira_mao(a, 110.0, d_a)
        engine._despachar_primeira_mao(b, 110.0, d_b)

        assert set(d_a) == set(d_b) == {"Joinha"}

    def test_mao_unica_dispara_normalmente(self, engine):
        disparos = {}
        engine._despachar_primeira_mao({"Right": mao("V")}, 110.0, disparos)
        assert set(disparos) == {"V"}

    def test_nenhuma_mao_nao_dispara(self, engine):
        disparos = {}
        engine._despachar_primeira_mao({}, 110.0, disparos)
        assert disparos == {}


class TestGestoDesabilitado:
    def test_mao_com_gesto_desabilitado_e_ignorada(self):
        """Se a mão que chegou primeiro tem gesto desligado, a outra assume."""
        e = engine_de_teste(
            bindings={"V": binding(enabled=False), "Joinha": binding()}
        )
        try:
            maos = {
                "Left": mao("V", inicio=100.0),  # primeiro, mas desabilitado
                "Right": mao("Joinha", inicio=105.0),
            }
            disparos = {}
            e._despachar_primeira_mao(maos, 110.0, disparos)
            assert set(disparos) == {"Joinha"}
        finally:
            e.action_executor.shutdown(wait=False)

    def test_todos_desabilitados_nao_dispara(self):
        e = engine_de_teste(bindings={"V": binding(enabled=False)})
        try:
            disparos = {}
            e._despachar_primeira_mao({"Left": mao("V")}, 110.0, disparos)
            assert disparos == {}
        finally:
            e.action_executor.shutdown(wait=False)


class TestInteracaoComHoldEEstabilidade:
    def test_mao_vencedora_ainda_precisa_completar_o_hold(self, engine):
        """Vencer o desempate não pula as outras proteções."""
        maos = {"Left": mao("V", inicio=100.0)}
        disparos = {}
        engine._despachar_primeira_mao(maos, 100.5, disparos)  # hold é 1.0s
        assert disparos == {}

    def test_mao_vencedora_ainda_precisa_estar_estavel(self, engine):
        maos = {"Left": mao("V", estavel=False, inicio=100.0)}
        disparos = {}
        engine._despachar_primeira_mao(maos, 110.0, disparos)
        assert disparos == {}

    def test_vencedora_instavel_nao_passa_a_vez(self, engine):
        """A primeira mão vence o desempate mesmo se ainda não estiver pronta.

        Comportamento deliberado: sem isso, tremer a mão que começou primeiro faria a
        ação da OUTRA mão disparar, o que é surpreendente. Nada dispara até a mão que
        está na frente ficar pronta ou desistir do gesto.
        """
        maos = {
            "Left": mao("V", estavel=False, inicio=100.0),
            "Right": mao("Joinha", estavel=True, inicio=105.0),
        }
        disparos = {}
        engine._despachar_primeira_mao(maos, 110.0, disparos)
        assert disparos == {}


class TestCooldownCompartilhado:
    def test_mesmo_gesto_nas_duas_maos_dispara_uma_vez(self, engine):
        """Continua valendo o D-02: cooldown por gesto, primeira mão vence."""
        maos = {
            "Left": mao("Joinha", inicio=100.0),
            "Right": mao("Joinha", inicio=100.5),
        }
        disparos = {}
        engine._despachar_primeira_mao(maos, 110.0, disparos)
        engine._despachar_primeira_mao(maos, 110.1, disparos)

        assert set(disparos) == {"Joinha"}
