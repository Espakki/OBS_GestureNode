"""A fronteira de plataforma. Ver D-42.

O que estes testes protegem não é o código Win32 — esse só se prova no Windows real. É a
**disciplina de import**: nenhum módulo do app pode carregar API de um sistema operacional
no topo, porque isso derruba o app antes de a janela abrir em qualquer outro sistema.
"""

import ast
import sys
from pathlib import Path

import pytest

import plataforma

RAIZ = Path(__file__).resolve().parent.parent

# Módulos que só existem em um sistema. Importar qualquer um deles no nível de módulo,
# fora de `plataforma/`, é o bug que motivou toda esta camada.
IMPORTS_DE_SISTEMA = {"winsound", "msvcrt", "winreg", "fcntl", "termios", "grp", "pwd"}

# Pacotes do app que precisam carregar em qualquer sistema.
PACOTES_PORTATEIS = ("core", "engine", "actions", "integrations", "util", "ui")


def _arquivos_portateis():
    for pacote in PACOTES_PORTATEIS:
        yield from (RAIZ / pacote).rglob("*.py")


def _imports_no_topo(caminho):
    """Nomes importados no nível do módulo — ignora os que estão dentro de função."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    nomes = set()
    for no in arvore.body:  # só o corpo do módulo, não `ast.walk`
        if isinstance(no, ast.Import):
            nomes.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module.split(".")[0])
        elif isinstance(no, ast.Try):
            # `try: import x / except: x = None` é import guardado — aceitável.
            continue
    return nomes


class TestDisciplinaDeImport:
    def test_nenhum_modulo_portatil_importa_api_de_sistema(self):
        """O bug original: `import winsound` no topo de `actions/action_manager.py`.

        Como a cadeia `main.py → ui → engine → action_manager` é toda import de nível de
        módulo, isso derrubava o app no Linux **antes de a janela abrir**.
        """
        infratores = {}
        for arquivo in _arquivos_portateis():
            proibidos = _imports_no_topo(arquivo) & IMPORTS_DE_SISTEMA
            if proibidos:
                infratores[str(arquivo.relative_to(RAIZ))] = sorted(proibidos)

        assert not infratores, (
            "módulos portáteis importando API de sistema no topo: " f"{infratores}"
        )

    def test_o_pacote_plataforma_pode_importar_o_que_quiser(self):
        """A exceção existe e é o ponto: `_windows.py` só é importado no Windows."""
        windows = RAIZ / "plataforma" / "_windows.py"
        assert "winsound" in _imports_no_topo(windows)

    def test_action_manager_nao_conhece_mais_o_sistema(self):
        """Ele virou só despacho e parsing — nada de `ctypes`, `winsound` ou `platform`."""
        fonte = (RAIZ / "actions" / "action_manager.py").read_text(encoding="utf-8")
        for proibido in ("winsound", "ctypes", "WinDLL", "SendInput"):
            assert proibido not in fonte, f"{proibido} ainda aparece em action_manager"


class TestInterface:
    """Toda implementação precisa oferecer o mesmo contrato."""

    FUNCOES = ("tocar_som", "enviar_atalho", "url_do_dispositivo")
    CONSTANTES = ("NOME", "FORMATO_CAPTURA")

    @pytest.mark.parametrize("modulo", ["_generico", "_windows"])
    def test_implementacoes_cumprem_o_contrato(self, modulo):
        if modulo == "_windows" and not sys.platform.startswith("win"):
            pytest.skip("_windows só importa no Windows, por construção")

        impl = __import__(f"plataforma.{modulo}", fromlist=[modulo])

        for nome in self.FUNCOES:
            assert callable(getattr(impl, nome, None)), f"{modulo} sem {nome}()"
        for nome in self.CONSTANTES:
            assert getattr(impl, nome, None), f"{modulo} sem {nome}"

    def test_fachada_expoe_o_que_o_app_usa(self):
        for nome in ("tocar_som", "enviar_atalho", "formato_de_captura",
                     "url_do_dispositivo", "nome"):
            assert callable(getattr(plataforma, nome, None))


class TestEnderecamentoDaCamera:
    """A diferença entre sistemas não é só sintaxe — é identidade.

    O DirectShow endereça a câmera por NOME; o v4l2 por NÚMERO. Um `/dev/video0` não sabe
    o que é "HD Pro Webcam C920", e o DirectShow não sabe o que é o índice 0.
    """

    def test_windows_usa_nome(self):
        if not sys.platform.startswith("win"):
            pytest.skip("específico do Windows")
        from plataforma import _windows

        assert _windows.url_do_dispositivo("HD Pro Webcam C920", 0) == "video=HD Pro Webcam C920"
        assert _windows.FORMATO_CAPTURA == "dshow"

    def test_generico_usa_indice(self):
        from plataforma import _generico

        assert _generico.url_do_dispositivo("HD Pro Webcam C920", 2) == "/dev/video2"
        assert _generico.FORMATO_CAPTURA == "v4l2"


class TestFallbackDeTeclado:
    def test_sem_pacote_keyboard_nao_estoura(self, monkeypatch):
        """Ausência de backend é aviso, não exceção — o gesto não pode derrubar a engine."""
        from plataforma import _generico

        monkeypatch.setattr(_generico, "keyboard", None)
        assert _generico.enviar_atalho(["ctrl"], "z") is False

    def test_som_no_generico_recusa_sem_estourar(self):
        from plataforma import _generico

        assert _generico.tocar_som("qualquer.wav") is False
