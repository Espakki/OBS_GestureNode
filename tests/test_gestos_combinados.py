"""Gestos combinados: o par de mãos tratado como uma unidade. Ver D-30.

O ponto delicado é a **supressão**: quando as duas mãos formam um par configurado, os
gestos individuais não podem disparar. Sem isso, segurar V numa mão e Joinha na outra
dispararia três ações — a de V, a de Joinha e a do combinado.
"""

import pytest

from core.gestos_combinados import chave_do_par, e_chave_de_par, par_da_chave
from engine.gesture_engine import GestureEngine


class TestChaveCanonica:
    def test_ordem_nao_importa(self):
        """Base do D-30: o par é não ordenado, seguindo o D-03."""
        assert chave_do_par("V", "Joinha") == chave_do_par("Joinha", "V")

    def test_formato_legivel(self):
        assert chave_do_par("Joinha", "V") == "Joinha + V"

    def test_ida_e_volta(self):
        chave = chave_do_par("Punho", "OK")
        assert set(par_da_chave(chave)) == {"Punho", "OK"}

    def test_mesmo_gesto_nas_duas_maos(self):
        """Joinha com as duas mãos é um par válido e distinto do Joinha sozinho."""
        assert chave_do_par("Joinha", "Joinha") == "Joinha + Joinha"
        assert par_da_chave("Joinha + Joinha") == ("Joinha", "Joinha")

    @pytest.mark.parametrize("lixo", ["", "V", "A + B + C", " + ", "V + "])
    def test_chave_corrompida_devolve_none(self, lixo):
        """Config editado à mão não pode virar unpacking com erro em runtime."""
        assert par_da_chave(lixo) is None
        assert e_chave_de_par(lixo) is False


def engine_de_teste(combined=None, bindings=None):
    """Engine em modo teste: detecta e conta disparos, mas não toca em OBS/som/atalho."""
    cfg = {
        "modo": "teste",
        "max_maos": 2,
        "camera": {"index": 0, "device_name": ""},
        "gestures": {
            "bindings": bindings or {},
            "default_hold_time": 2.0,
            "default_cooldown": 2.0,
        },
        "combined_bindings": combined or {},
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
        combined={"Joinha + V": binding()},
        bindings={"V": binding(), "Joinha": binding()},
    )
    yield e
    e.action_executor.shutdown(wait=False)


# (gesto, estavel, inicio_do_hold)
def mao(gesto, estavel=True, inicio=100.0):
    return (gesto, estavel, inicio)


class TestDeteccaoDoPar:
    def test_par_configurado_e_reconhecido(self, engine):
        combo = engine._combinado_candidato(
            {"Left": mao("V"), "Right": mao("Joinha")}, tempo_atual=100.0
        )
        assert combo is not None
        assert combo[0] == "Joinha + V"

    def test_ordem_das_maos_nao_importa(self, engine):
        """Mesmo par vindo trocado tem de dar a mesma chave (D-30)."""
        a = engine._combinado_candidato(
            {"Left": mao("V"), "Right": mao("Joinha")}, tempo_atual=100.0
        )
        b = engine._combinado_candidato(
            {"Left": mao("Joinha"), "Right": mao("V")}, tempo_atual=100.0
        )
        assert a[0] == b[0]

    def test_uma_mao_so_nao_forma_par(self, engine):
        assert engine._combinado_candidato({"Left": mao("V")}, tempo_atual=100.0) is None

    def test_par_sem_binding_nao_e_candidato(self, engine):
        combo = engine._combinado_candidato(
            {"Left": mao("Punho"), "Right": mao("OK")}, tempo_atual=100.0
        )
        assert combo is None

    def test_par_desabilitado_nao_e_candidato(self):
        e = engine_de_teste(combined={"Joinha + V": binding(enabled=False)})
        try:
            combo = e._combinado_candidato(
                {"Left": mao("V"), "Right": mao("Joinha")}, tempo_atual=100.0
            )
            assert combo is None
        finally:
            e.action_executor.shutdown(wait=False)


class TestHoldDoCombinado:
    def test_hold_conta_do_instante_em_que_o_par_se_formou(self, engine):
        """Não do início do gesto de cada mão.

        As mãos raramente fecham o gesto no mesmo frame; usar o início de uma delas daria
        vantagem arbitrária à que chegou primeiro.
        """
        maos = {"Left": mao("V", inicio=10.0), "Right": mao("Joinha", inicio=50.0)}

        combo = engine._combinado_candidato(maos, tempo_atual=100.0)
        assert combo[2] == 100.0, "o hold começa quando o par se forma"

        # frames seguintes mantêm o mesmo início
        combo = engine._combinado_candidato(maos, tempo_atual=100.5)
        assert combo[2] == 100.0

    def test_trocar_de_par_reinicia_o_hold(self):
        e = engine_de_teste(
            combined={"Joinha + V": binding(), "OK + Punho": binding()}
        )
        try:
            e._combinado_candidato(
                {"Left": mao("V"), "Right": mao("Joinha")}, tempo_atual=100.0
            )
            combo = e._combinado_candidato(
                {"Left": mao("OK"), "Right": mao("Punho")}, tempo_atual=105.0
            )
            assert combo[2] == 105.0
        finally:
            e.action_executor.shutdown(wait=False)

    def test_par_instavel_e_reportado_como_instavel(self, engine):
        combo = engine._combinado_candidato(
            {"Left": mao("V", estavel=True), "Right": mao("Joinha", estavel=False)},
            tempo_atual=100.0,
        )
        assert combo[3] is False, "basta uma mão tremendo para o par não estar estável"


class TestDisparo:
    def test_dispara_apos_o_hold(self, engine):
        disparos = {}
        engine._tentar_disparar("X", binding(hold_time=1.0), 100.0, True, 101.5, disparos)
        assert "X" in disparos

    def test_nao_dispara_antes_do_hold(self, engine):
        disparos = {}
        engine._tentar_disparar("X", binding(hold_time=2.0), 100.0, True, 101.0, disparos)
        assert disparos == {}

    def test_nao_dispara_com_mao_instavel(self, engine):
        disparos = {}
        engine._tentar_disparar("X", binding(hold_time=1.0), 100.0, False, 105.0, disparos)
        assert disparos == {}

    def test_cooldown_bloqueia_repeticao(self, engine):
        disparos = {"X": 100.0}
        engine._tentar_disparar("X", binding(hold_time=0.5, cooldown=5.0), 100.0, True, 102.0, disparos)
        assert disparos["X"] == 100.0, "não deveria ter redisparado"

    def test_cooldown_expirado_libera(self, engine):
        disparos = {"X": 100.0}
        engine._tentar_disparar("X", binding(hold_time=0.5, cooldown=1.0), 100.0, True, 110.0, disparos)
        assert disparos["X"] == 110.0

    def test_binding_vazio_nao_dispara(self, engine):
        disparos = {}
        engine._tentar_disparar("X", {}, 100.0, True, 200.0, disparos)
        assert disparos == {}


class TestSupressaoDosIndividuais:
    """O comportamento que justifica a feature existir.

    Sem supressão, formar um par dispararia três ações: as duas individuais e a do
    combinado — provavelmente trocando de cena três vezes.
    """

    def test_combinado_e_individuais_compartilham_o_registro_de_disparo(self, engine):
        """Combinado e individual convivem no mesmo dict de cooldown, sem colidir.

        A chave do par contém " + ", que nenhum nome de gesto individual tem, então não
        há risco de um sobrescrever o outro.
        """
        disparos = {}
        engine._tentar_disparar("V", binding(hold_time=0.5), 100.0, True, 101.0, disparos)
        engine._tentar_disparar("Joinha + V", binding(hold_time=0.5), 100.0, True, 101.0, disparos)

        assert set(disparos) == {"V", "Joinha + V"}

    def test_par_reconhecido_bloqueia_o_caminho_individual(self, engine):
        """Quando há combinado candidato, o loop não entra no ramo individual.

        Espelha a estrutura do `run()`: se `_combinado_candidato` devolve algo, os
        individuais são pulados — mesmo que já tivessem completado o próprio hold.
        """
        maos = {"Left": mao("V"), "Right": mao("Joinha")}
        combo = engine._combinado_candidato(maos, tempo_atual=100.0)

        disparos = {}
        if combo is not None:
            chave, cfg, inicio, estavel = combo
            engine._tentar_disparar(chave, cfg, inicio, estavel, 102.0, disparos)
        else:
            for gesto, estavel, inicio in maos.values():
                engine._tentar_disparar(
                    gesto, engine._resolver_binding(gesto), inicio, estavel, 102.0, disparos
                )

        assert set(disparos) == {"Joinha + V"}
        assert "V" not in disparos and "Joinha" not in disparos

    def test_sem_par_configurado_os_individuais_disparam(self, engine):
        """Duas mãos sem combinado configurado seguem o fluxo do D-03: cada uma dispara."""
        maos = {"Left": mao("Punho"), "Right": mao("OK")}
        combo = engine._combinado_candidato(maos, tempo_atual=100.0)
        assert combo is None

        disparos = {}
        for gesto, estavel, inicio in maos.values():
            engine._tentar_disparar(gesto, binding(hold_time=0.5), inicio, estavel, 102.0, disparos)

        assert set(disparos) == {"Punho", "OK"}
