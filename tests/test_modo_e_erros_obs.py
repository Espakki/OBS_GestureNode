"""Migração de modo legado e classificação de erros do OBS.

A migração vivia duplicada em `ui/mixins/config_mixin.py` e `engine/gesture_engine.py`,
e as duas cópias haviam divergido de verdade — a da UI não fazia `.lower()`. Agora existe
só `core.modos.migrar_modo`, e estes testes exercitam a função real. Ver D-27.
"""

import pytest

from core.modos import MODOS_VALIDOS, migrar_modo
from integrations.obs_connect_thread import _classificar_erro

LEGADO = {"test": "teste", "obs": "automatico"}


class TestMigracaoDeModo:
    @pytest.mark.parametrize("antigo,novo", list(LEGADO.items()))
    def test_valores_legados_migram(self, antigo, novo):
        assert migrar_modo(antigo) == novo

    @pytest.mark.parametrize("modo", sorted(MODOS_VALIDOS))
    def test_valores_validos_passam_intactos(self, modo):
        assert migrar_modo(modo) == modo

    @pytest.mark.parametrize("lixo", ["", None, "xyz", "OBS_MODE", 42])
    def test_valor_desconhecido_vira_automatico(self, lixo):
        assert migrar_modo(lixo) == "automatico"

    @pytest.mark.parametrize(
        "entrada,esperado",
        [("TESTE", "teste"), ("Manual", "manual"), ("OBS", "automatico"), ("Test", "teste")],
    )
    def test_maiusculas_sao_aceitas(self, entrada, esperado):
        """Regressão da divergência que motivou o D-27.

        A cópia da UI não fazia `.lower()`, então `"TESTE"` virava `"automatico"` nela e
        `"teste"` na engine. O usuário via "Automático" na interface enquanto o motor
        rodava com as ações bloqueadas.
        """
        assert migrar_modo(entrada) == esperado

    def test_espaco_em_volta_e_tolerado(self):
        assert migrar_modo("  manual  ") == "manual"

    def test_uma_unica_implementacao(self):
        """UI e engine têm de usar a mesma função — não uma cópia local.

        Se alguém reintroduzir a regra inline em um dos dois, este teste não pega, mas a
        divergência volta. Aqui garantimos ao menos que ambos importam a fonte única.
        """
        import engine.gesture_engine as eng
        import ui.mixins.config_mixin as cfg

        assert eng.migrar_modo is migrar_modo
        assert cfg.migrar_modo is migrar_modo


class TestClassificacaoDeErroOBS:
    """Cada erro precisa virar uma frase que diga ao usuário o que fazer (D-14)."""

    def test_conexao_recusada_manda_abrir_o_obs(self):
        msg = _classificar_erro(ConnectionRefusedError())
        assert "OBS" in msg and "WebSocket" in msg

    def test_timeout_aponta_para_ip_e_porta(self):
        msg = _classificar_erro(TimeoutError())
        assert "Timeout" in msg

    def test_dns_aponta_para_o_campo_host(self):
        msg = _classificar_erro(OSError("getaddrinfo failed"))
        assert "Host" in msg or "Endereço" in msg

    def test_erro_desconhecido_tem_fallback(self):
        msg = _classificar_erro(ValueError("algo inesperado"))
        assert msg
        assert "Falha" in msg

    def test_nunca_devolve_stack_trace(self):
        """A mensagem vai para a UI — não pode vazar detalhe técnico cru."""
        for exc in [ConnectionRefusedError(), TimeoutError(), OSError(), ValueError()]:
            msg = _classificar_erro(exc)
            assert "Traceback" not in msg
            assert len(msg) < 200
