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

    @pytest.mark.parametrize("modulo", ["_generico", "_windows", "_linux"])
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


class TestLinuxSessaoEBackends:
    """Qual injetor tentar, e em que ordem. Ver D-46.

    O `_linux` não toca em API nativa — só monta comandos —, então toda esta lógica roda e
    é testável no Windows. O que nenhum destes testes prova é que o comando montado
    funciona de verdade; isso exige Linux real.
    """

    VARIAVEIS = ("XDG_SESSION_TYPE", "WAYLAND_DISPLAY", "DISPLAY")

    @pytest.fixture
    def ambiente_limpo(self, monkeypatch):
        for variavel in self.VARIAVEIS:
            monkeypatch.delenv(variavel, raising=False)
        return monkeypatch

    def test_xdg_session_type_tem_a_palavra_final(self, ambiente_limpo):
        """DISPLAY definido numa sessão Wayland é rotina — o XWayland define.

        Confiar nele em vez do `XDG_SESSION_TYPE` escolheria o backend errado justamente
        no caso mais comum de desktop moderno.
        """
        from plataforma import _linux

        ambiente_limpo.setenv("XDG_SESSION_TYPE", "wayland")
        ambiente_limpo.setenv("DISPLAY", ":0")
        assert _linux.sessao_grafica() == "wayland"

    def test_sem_xdg_as_variaveis_de_display_decidem(self, ambiente_limpo):
        from plataforma import _linux

        ambiente_limpo.setenv("WAYLAND_DISPLAY", "wayland-0")
        assert _linux.sessao_grafica() == "wayland"

        ambiente_limpo.delenv("WAYLAND_DISPLAY")
        ambiente_limpo.setenv("DISPLAY", ":0")
        assert _linux.sessao_grafica() == "x11"

    def test_sem_nada_a_sessao_e_desconhecida(self, ambiente_limpo):
        from plataforma import _linux

        assert _linux.sessao_grafica() == "desconhecida"

    def test_cada_sessao_tenta_o_backend_nativo_primeiro(self):
        from plataforma import _linux

        assert _linux.backends_preferidos("x11")[0] == "xdotool"
        assert _linux.backends_preferidos("wayland")[0] == "wtype"

    def test_ydotool_e_sempre_o_ultimo(self):
        """Funciona em toda sessão, mas exige daemon e permissão no uinput."""
        from plataforma import _linux

        for sessao in ("x11", "wayland", "desconhecida"):
            assert _linux.backends_preferidos(sessao)[-1] == "ydotool"

    def test_sessao_desconhecida_tenta_todos(self):
        from plataforma import _linux

        assert set(_linux.backends_preferidos("desconhecida")) == set(_linux.BACKENDS)


class TestLinuxMontagemDeComando:
    """A forma exata da linha de comando de cada injetor."""

    def test_xdotool_junta_a_combinacao_num_argumento(self):
        from plataforma import _linux

        assert _linux.comando_xdotool(["ctrl", "shift"], "f5") == [
            "xdotool", "key", "ctrl+shift+F5",
        ]

    def test_wtype_solta_os_modificadores_na_ordem_inversa(self):
        """O `wtype` não desfaz o que o `-M` segurou; modificador preso vaza pro resto."""
        from plataforma import _linux

        assert _linux.comando_wtype(["ctrl", "shift"], "f5") == [
            "wtype", "-M", "ctrl", "-M", "shift", "-k", "F5", "-m", "shift", "-m", "ctrl",
        ]

    def test_ydotool_emite_cada_evento_com_pressiona_e_solta(self):
        from plataforma import _linux

        # 29 = KEY_LEFTCTRL, 42 = KEY_LEFTSHIFT, 63 = KEY_F5 (59 + 4).
        assert _linux.comando_ydotool(["ctrl", "shift"], "f5") == [
            "ydotool", "key", "29:1", "42:1", "63:1", "63:0", "42:0", "29:0",
        ]

    def test_a_tecla_windows_tem_nome_diferente_em_cada_backend(self):
        """Mesma tecla física, três vocabulários: super, logo e o código do kernel."""
        from plataforma import _linux

        assert _linux.comando_xdotool(["windows"], "d")[-1] == "super+d"
        assert "logo" in _linux.comando_wtype(["windows"], "d")
        assert _linux.comando_ydotool(["windows"], "d")[2] == "125:1"

    def test_tecla_desconhecida_devolve_none_em_vez_de_comando_torto(self):
        """`None` faz o chamador pular o backend; comando inválido gastaria o timeout."""
        from plataforma import _linux

        montadores = (
            _linux.comando_xdotool,
            _linux.comando_wtype,
            _linux.comando_ydotool,
        )
        for montar in montadores:
            assert montar(["ctrl"], "tecla que nao existe") is None
            assert montar(["ctrl"], "") is None

    def test_modificador_desconhecido_e_ignorado_sem_derrubar(self):
        from plataforma import _linux

        assert _linux.comando_xdotool(["ctrl", "hiper"], "a") == ["xdotool", "key", "ctrl+a"]


class TestLinuxMapaDeTeclas:
    def test_as_teclas_de_funcao_pulam_as_faixas_do_kernel(self):
        """F1-F10, F11-F12 e F13-F24 moram em faixas separadas do input-event-codes.h.

        Tratar como contíguo é o erro fácil aqui: daria 69 para o F11, que é o Num Lock.
        """
        from plataforma import _linux

        assert _linux.token_para_keycode("f1") == 59
        assert _linux.token_para_keycode("f10") == 68
        assert _linux.token_para_keycode("f11") == 87
        assert _linux.token_para_keycode("f12") == 88
        assert _linux.token_para_keycode("f13") == 183
        assert _linux.token_para_keycode("f24") == 194

    def test_f25_nao_existe(self):
        from plataforma import _linux

        assert _linux.token_para_keycode("f25") is None
        assert _linux.token_para_keysym("f25") is None

    def test_mais_e_igual_sao_a_mesma_tecla_fisica(self):
        """Espelha o Windows, onde ambos viram VK 0xBB."""
        from plataforma import _linux

        assert _linux.token_para_keycode("+") == _linux.token_para_keycode("=")

    def test_tokens_de_duas_palavras_do_action_manager_sao_conhecidos(self):
        """`page up`, `print screen` e companhia saem assim de `_normalizar_atalho`."""
        from plataforma import _linux

        for token in ("page up", "page down", "print screen", "scroll lock",
                      "caps lock", "num lock"):
            assert _linux.token_para_keysym(token), f"keysym faltando para {token}"
            assert _linux.token_para_keycode(token), f"keycode faltando para {token}"

    def test_paridade_com_o_windows(self):
        """Toda tecla que o Windows sabe enviar, o Linux também precisa saber.

        Sem isto, um atalho configurado no Windows viraria silêncio no Linux — e o
        `config.json` é o mesmo arquivo, então a combinação atravessa os dois sistemas.
        """
        if not sys.platform.startswith("win"):
            pytest.skip("precisa do _windows, que só importa no Windows")
        from plataforma import _linux, _windows

        faltando = [
            token for token in _windows.VK_NOMEADAS
            if _linux.token_para_keysym(token) is None
            or _linux.token_para_keycode(token) is None
        ]
        assert not faltando, f"o Linux não sabe representar: {faltando}"


class TestLinuxEnvioDeAtalho:
    def test_backend_que_falha_nao_encerra_a_tentativa(self, monkeypatch):
        """No Wayland do GNOME o `wtype` existe e sai com erro — quem resolve é o próximo."""
        from plataforma import _linux

        monkeypatch.setattr(
            _linux, "backends_preferidos", lambda sessao=None: ["wtype", "ydotool"]
        )
        monkeypatch.setattr(_linux.shutil, "which", lambda programa: f"/usr/bin/{programa}")

        chamados = []

        def falso_executar(comando):
            chamados.append(comando[0])
            return comando[0].endswith("ydotool")

        monkeypatch.setattr(_linux, "_executar", falso_executar)

        assert _linux.enviar_atalho(["ctrl"], "a") is True
        assert chamados == ["/usr/bin/wtype", "/usr/bin/ydotool"]

    def test_backend_nao_instalado_e_pulado_sem_executar(self, monkeypatch):
        from plataforma import _linux

        monkeypatch.setattr(
            _linux, "backends_preferidos", lambda sessao=None: ["wtype", "ydotool"]
        )
        monkeypatch.setattr(
            _linux.shutil,
            "which",
            lambda programa: "/usr/bin/ydotool" if programa == "ydotool" else None,
        )

        chamados = []

        def falso_executar(comando):
            chamados.append(comando[0])
            return True

        monkeypatch.setattr(_linux, "_executar", falso_executar)

        assert _linux.enviar_atalho(["ctrl"], "a") is True
        assert chamados == ["/usr/bin/ydotool"]

    def test_sem_injetor_nenhum_cai_no_generico_sem_estourar(self, monkeypatch):
        """Gesto sem backend é aviso e `False` — nunca exceção subindo pela engine."""
        from plataforma import _generico, _linux

        monkeypatch.setattr(_linux.shutil, "which", lambda programa: None)
        monkeypatch.setattr(_generico, "keyboard", None)

        assert _linux.enviar_atalho(["ctrl"], "a") is False

    def test_timeout_do_injetor_nao_trava_a_thread(self, monkeypatch):
        """Um `xdotool` pendurado seguraria a thread de ações; o corte devolve False."""
        import subprocess

        from plataforma import _linux

        def travar(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="xdotool", timeout=_linux.TIMEOUT_SEGUNDOS)

        monkeypatch.setattr(_linux.subprocess, "run", travar)
        assert _linux._executar(["/usr/bin/xdotool", "key", "a"]) is False


class TestLinuxAudio:
    def test_arquivo_ausente_avisa_em_vez_de_estourar(self):
        from plataforma import _linux

        assert _linux.tocar_som("/tmp/nao-existe-mesmo.wav") is False
        assert _linux.tocar_som("") is False

    def test_wav_prefere_o_servidor_de_som_e_comprimido_prefere_o_decodificador(self):
        """`paplay` e `aplay` só tocam PCM: um mp3 neles falharia."""
        from plataforma import _linux

        assert _linux.tocadores_para("beep.wav")[0][0] == "paplay"
        assert _linux.tocadores_para("beep.mp3")[0][0] == "ffplay"
        assert _linux.tocadores_para("BEEP.WAV")[0][0] == "paplay"

    def test_sem_tocador_instalado_devolve_false(self, monkeypatch, tmp_path):
        from plataforma import _linux

        som = tmp_path / "beep.wav"
        som.write_bytes(b"RIFF")
        monkeypatch.setattr(_linux.shutil, "which", lambda programa: None)

        assert _linux.tocar_som(str(som)) is False


class TestLinuxCamera:
    def test_endereca_por_no_e_nao_por_nome(self):
        from plataforma import _linux

        assert _linux.url_do_dispositivo("HD Pro Webcam C920", 2) == "/dev/video2"
        assert _linux.FORMATO_CAPTURA == "v4l2"
