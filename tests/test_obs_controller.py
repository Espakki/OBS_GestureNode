"""Troca de cena no OBS: requisição recusada não pode derrubar a conexão. Ver D-37."""

import pytest
from obsws_python.error import OBSSDKRequestError

from integrations.obs_controller import OBSController


class ClienteFalso:
    def __init__(self, erro=None):
        self.erro = erro
        self.cenas_pedidas = []

    def set_current_program_scene(self, nome):
        self.cenas_pedidas.append(nome)
        if self.erro is not None:
            raise self.erro


def controlador(erro=None):
    c = OBSController(host="localhost", port=4455, password="")
    c.cliente = ClienteFalso(erro)
    c.connected = True
    return c


class TestTrocaBemSucedida:
    def test_devolve_ok_e_troca(self):
        c = controlador()
        ok, mensagem = c.trocar_cena("Cena 1")

        assert ok is True
        assert mensagem == ""
        assert c.cliente.cenas_pedidas == ["Cena 1"]

    def test_conexao_permanece(self):
        c = controlador()
        c.trocar_cena("Cena 1")
        assert c.connected is True


class TestCenaInexistente:
    """O bug que motivou o D-37.

    O usuário digitava um nome de cena que o OBS não tinha, o gesto disparava, e a
    conexão inteira morria. Ele corrigia o nome e continuava sem funcionar — porque já
    não havia conexão. Só reiniciar a engine resolvia, o que parecia "a config não salva".
    """

    ERRO = OBSSDKRequestError("SetCurrentProgramScene", 600, "scene not found")

    def test_nao_derruba_a_conexao(self):
        c = controlador(erro=self.ERRO)

        ok, _ = c.trocar_cena("Cena Que Nao Existe")

        assert ok is False
        assert c.connected is True, "requisição recusada não é conexão perdida"
        assert c.cliente is not None

    def test_a_proxima_troca_ainda_funciona(self):
        """A prova de que a conexão sobreviveu: trocar de novo tem de chegar ao OBS."""
        c = controlador(erro=self.ERRO)
        c.trocar_cena("Cena Errada")

        c.cliente.erro = None
        ok, _ = c.trocar_cena("Cena Certa")

        assert ok is True
        assert c.cliente.cenas_pedidas == ["Cena Errada", "Cena Certa"]

    def test_mensagem_diz_qual_cena_falhou(self):
        c = controlador(erro=self.ERRO)
        _, mensagem = c.trocar_cena("Minha Cena")

        assert "Minha Cena" in mensagem
        assert "não tem" in mensagem


class TestConexaoPerdida:
    def test_erro_de_conexao_derruba_mesmo(self):
        """Aqui derrubar é o certo — reconectar é responsabilidade de quem chamou."""
        c = controlador(erro=ConnectionResetError("socket fechado"))

        ok, mensagem = c.trocar_cena("Cena 1")

        assert ok is False
        assert c.connected is False
        assert c.cliente is None
        assert "caiu" in mensagem

    def test_sem_conexao_nao_estoura(self):
        c = OBSController(host="localhost", port=4455, password="")
        ok, mensagem = c.trocar_cena("Cena 1")

        assert ok is False
        assert "não conectado" in mensagem
