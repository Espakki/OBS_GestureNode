"""Atalhos de teclado: captura na UI e normalização para envio.

Migrado de `teste/test_hotkey_capture_logic.py` e `teste/test_hotkey_dispatch.py`, que
eram scripts manuais. É lógica pura (parsing de texto e eventos de tecla), então não havia
razão para exigir execução na mão — e enquanto ficou lá, teve **zero cobertura
automática**. Ver D-43.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt  # noqa: E402
from PySide6.QtGui import QKeyEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from actions.action_manager import ActionManager  # noqa: E402
from ui.tabs.gestos_tab import HotkeyLineEdit  # noqa: E402


@pytest.fixture(scope="session")
def app_qt():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def normalizar():
    return ActionManager(None, modo="automatico")._normalizar_atalho


class TestNormalizacao:
    """Texto vindo da UI vira uma combinação canônica para o envio."""

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("Ctrl+Shift+Z", "ctrl+shift+z"),
            ("Ctrl+Shift+A", "ctrl+shift+a"),
            ("Ctrl+F12", "ctrl+f12"),
            ("Ctrl+/", "ctrl+/"),
            ("Ctrl+Delete", "ctrl+delete"),
        ],
    )
    def test_combinacoes_comuns(self, normalizar, entrada, esperado):
        assert normalizar(entrada) == esperado

    def test_ordem_dos_modificadores_e_deterministica(self, normalizar):
        """Sempre ctrl, alt, shift, windows — independente de como veio.

        Sem isso, a mesma combinação capturada de dois jeitos viraria dois atalhos
        diferentes no config, e o usuário não teria como saber por quê.
        """
        assert normalizar("Shift+Ctrl+Alt+F") == "ctrl+alt+shift+f"
        assert normalizar("Alt+Shift+Ctrl+F") == "ctrl+alt+shift+f"

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("Ctrl+PageUp", "ctrl+page up"),
            ("Ctrl+PgDown", "ctrl+page down"),
            ("Ctrl+Shift+Plus", "ctrl+shift++"),
        ],
    )
    def test_apelidos_de_tecla(self, normalizar, entrada, esperado):
        assert normalizar(entrada) == esperado

    @pytest.mark.parametrize("incompleto", ["Ctrl+Alt", "Ctrl", "", "Shift+Ctrl"])
    def test_combinacao_sem_tecla_final_e_recusada(self, normalizar, incompleto):
        """"Ctrl+Alt" não é atalho — é modificador solto, e enviar isso trava teclas."""
        assert normalizar(incompleto) is None


class TestCapturaNaInterface:
    """O `HotkeyLineEdit` traduz eventos de tecla no texto que vai para o config."""

    @staticmethod
    def _capturar(campo, tecla_final, texto_final, com_alt=False):
        campo._start_capture()

        mods = Qt.ControlModifier | Qt.ShiftModifier
        campo.keyPressEvent(
            QKeyEvent(QEvent.KeyPress, Qt.Key_Control, Qt.ControlModifier, "")
        )
        if com_alt:
            mods |= Qt.AltModifier
            campo.keyPressEvent(
                QKeyEvent(
                    QEvent.KeyPress, Qt.Key_Alt, Qt.ControlModifier | Qt.AltModifier, ""
                )
            )
        campo.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Shift, mods, ""))
        campo.keyPressEvent(QKeyEvent(QEvent.KeyPress, tecla_final, mods, texto_final))
        return campo.text()

    @pytest.mark.parametrize(
        "tecla,texto,esperado",
        [
            (Qt.Key_F, "f", "Ctrl+Shift+F"),
            (Qt.Key_Z, "z", "Ctrl+Shift+Z"),
            (Qt.Key_Q, "q", "Ctrl+Shift+Q"),
        ],
    )
    def test_captura_ctrl_shift(self, app_qt, tecla, texto, esperado):
        assert self._capturar(HotkeyLineEdit(), tecla, texto) == esperado

    @pytest.mark.parametrize(
        "tecla,texto,esperado",
        [
            (Qt.Key_Z, "z", "Ctrl+Alt+Shift+Z"),
            (Qt.Key_W, "w", "Ctrl+Alt+Shift+W"),
        ],
    )
    def test_captura_com_alt(self, app_qt, tecla, texto, esperado):
        assert self._capturar(HotkeyLineEdit(), tecla, texto, com_alt=True) == esperado

    def test_altgr_nao_corrompe_a_tecla(self, app_qt):
        """Regressão do bug de AltGr (commit `8838edf`).

        Em layouts como o ABNT2, Ctrl+Alt funciona como AltGr e o Qt entrega o **caractere
        composto** no texto do evento — `æ` no lugar de `z`. Gravar isso no config
        produziria um atalho que nunca casa com o registrado no OBS.

        O campo tem de usar o *código* da tecla, não o texto digitado.
        """
        resultado = self._capturar(HotkeyLineEdit(), Qt.Key_Z, "æ", com_alt=True)
        assert resultado == "Ctrl+Alt+Shift+Z"


class TestTraducaoPura:
    """A regra sem widget nenhum. Ver D-50.

    Estes testes existem porque a captura passou a ter **duas** implementações: o
    `HotkeyLineEdit` de Widgets e a de QML. Testar só pelo widget deixaria a versão QML
    descoberta — e o teste continuaria verde exercitando código que o app não usa mais.
    """

    def test_letra_com_modificadores(self):
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        assert atalho_capturado.montar(
            Qt.Key_F, Qt.ControlModifier | Qt.ShiftModifier, "f", 0x46
        ) == "Ctrl+Shift+F"

    def test_ordem_dos_modificadores_e_canonica(self):
        """O config compara atalho como string: "Shift+Ctrl+A" nunca casaria."""
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        todos = (
            Qt.ShiftModifier | Qt.MetaModifier | Qt.AltModifier | Qt.ControlModifier
        )
        assert atalho_capturado.montar(Qt.Key_A, todos, "a", 0x41) == "Ctrl+Alt+Shift+Win+A"

    def test_altgr_nao_corrompe_a_tecla(self):
        """A regressão do commit `8838edf`, agora na função e não no widget.

        **O código da tecla vem corrompido, não só o texto.** Em ABNT2 com AltGr, o Qt
        reporta `Key_AE` (198) — fora da faixa A-Z — e entrega `æ` no texto. Só o virtual
        key nativo ainda diz `Z`, que é a tecla que o dedo apertou.

        Este caso é o que prova a defesa. Um teste com `Key_Z` **não prova**: 90 está na
        faixa A-Z e a função retorna "Z" na primeira linha, sem nunca consultar o virtual
        key nativo. Verificado por mutação: apagar a consulta ao vk nativo mantinha o teste
        com `Key_Z` verde, e derruba este.
        """
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        combinado = Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier
        assert atalho_capturado.montar(
            Qt.Key_AE, combinado, "æ", native_vk=0x5A
        ) == "Ctrl+Alt+Shift+Z"

    def test_altgr_com_codigo_intacto_tambem_funciona(self):
        """O caminho fácil: quando o Qt acerta o código, o texto corrompido é ignorado."""
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        combinado = Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier
        assert atalho_capturado.montar(
            Qt.Key_Z, combinado, "æ", native_vk=0x5A
        ) == "Ctrl+Alt+Shift+Z"

    def test_caractere_de_layout_sem_vk_nativo_e_recusado(self):
        """Sem o virtual key para corrigir, gravar `æ` seria pior que não gravar nada.

        Um atalho com caractere composto nunca casa com o registrado no OBS, e o usuário
        fica com um gesto mudo, sem mensagem de erro.

        Nota de honestidade: duas verificações independentes recusam este caso — a que
        descarta não-ASCII de um caractere e a que só aceita ASCII no fim. A mutação de
        qualquer uma delas isolada não derruba este teste, porque a outra ainda segura.
        """
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        assert atalho_capturado.nome_da_tecla(Qt.Key_AE, texto="æ", native_vk=0) == ""

    def test_tecla_sem_modificador_nao_vira_atalho(self):
        """Uma letra solta dispararia o gesto toda vez que o usuário a digitasse."""
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        assert atalho_capturado.montar(Qt.Key_A, Qt.NoModifier, "a", 0x41) == ""

    def test_modificador_sozinho_nao_vira_atalho(self):
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        assert atalho_capturado.montar(Qt.Key_Control, Qt.ControlModifier, "", 0x11) == ""

    def test_teclas_de_funcao(self):
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        assert atalho_capturado.nome_da_tecla(Qt.Key_F5, native_vk=0x74) == "F5"
        assert atalho_capturado.nome_da_tecla(Qt.Key_F12, native_vk=0x7B) == "F12"

    def test_modificadores_segurados_valem_quando_as_flags_nao_chegaram(self):
        """Durante a captura, o usuário segura Ctrl+Shift antes de bater a tecla final."""
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        segurados = {Qt.Key_Control, Qt.Key_Shift}
        assert atalho_capturado.montar(
            Qt.Key_B, Qt.NoModifier, "b", 0x42, segurados=segurados
        ) == "Ctrl+Shift+B"

    def test_aceita_int_cru_alem_do_enum_do_qt(self):
        """As duas telas chamam com tipos diferentes. Ver D-50.

        O `HotkeyLineEdit` entrega `event.modifiers()`, que é um `KeyboardModifier`; a
        captura em QML entrega `int`, porque é o que atravessa a ponte. Sem normalizar,
        `int & enum` levanta TypeError -- e no caso das teclas seria pior: a comparação
        daria `False` em silêncio e o Ctrl deixaria de contar como modificador.
        """
        from PySide6.QtCore import Qt

        from ui import atalho_capturado

        flags = int(Qt.ControlModifier.value) | int(Qt.AltModifier.value)
        assert atalho_capturado.montar(
            int(Qt.Key_AE.value), flags, "æ", 0x5A
        ) == "Ctrl+Alt+Z"

        assert atalho_capturado.e_modificador(int(Qt.Key_Control.value)) is True
        assert atalho_capturado.e_modificador(Qt.Key_Control) is True
        assert atalho_capturado.e_modificador(int(Qt.Key_A.value)) is False
