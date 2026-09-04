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
