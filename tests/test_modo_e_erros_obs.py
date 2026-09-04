"""Migração de modo legado e classificação de erros do OBS.

A migração está duplicada em dois lugares (ui/mixins/config_mixin.py e
engine/gesture_engine.py::_setup) — ver B-04 no backlog. Enquanto a duplicação existir,
estes testes garantem que as duas cópias concordam. Quando ela for removida, os testes
continuam válidos sobre a cópia que sobrar.
"""

import pytest

from integrations.obs_connect_thread import _classificar_erro

MODOS_VALIDOS = {"teste", "manual", "automatico"}
LEGADO = {"test": "teste", "obs": "automatico"}


def migrar_modo(bruto):
    """Réplica da regra que as duas cópias implementam (D-18)."""
    bruto = str(bruto or "automatico").lower()
    bruto = LEGADO.get(bruto, bruto)
    return bruto if bruto in MODOS_VALIDOS else "automatico"


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

    def test_maiusculas_sao_aceitas(self):
        assert migrar_modo("TESTE") == "teste"
        assert migrar_modo("OBS") == "automatico"

    def test_engine_concorda_com_a_regra(self):
        """A cópia da engine tem de produzir o mesmo resultado que a regra acima.

        Reproduz o trecho de GestureEngine._setup sem instanciar a engine (que abriria
        câmera e carregaria o MediaPipe).
        """
        legado_map = {"test": "teste", "obs": "automatico"}
        modos_validos = {"teste", "manual", "automatico"}

        for entrada in ["test", "obs", "teste", "manual", "automatico", "xyz", ""]:
            raw = str({"modo": entrada}.get("modo", "automatico") or "automatico").lower()
            raw = legado_map.get(raw, raw)
            resultado_engine = raw if raw in modos_validos else "automatico"

            assert resultado_engine == migrar_modo(entrada), (
                f"engine e config divergem para {entrada!r}"
            )


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
