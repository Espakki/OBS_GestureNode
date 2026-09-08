"""OBS GestureNode — controle o OBS Studio por gestos de mão via webcam.

Copyright (C) 2026 Winicius Passaia

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo sob os termos da
Licença Pública Geral GNU, versão 3, publicada pela Free Software Foundation.

Distribuído na esperança de ser útil, mas SEM NENHUMA GARANTIA — sem sequer a garantia
implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO ESPECÍFICO. Veja a Licença
Pública Geral GNU para mais detalhes: <https://www.gnu.org/licenses/>.
"""

import sys

from PySide6.QtWidgets import QApplication

from core import config_store

from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET
from util.caminhos import caminho_do_config, migrar_config_legado
from util.logger import get_logger


logger = get_logger(__name__)

# Empacotado, isto resolve para %APPDATA% em vez de _internal/ dentro do bundle. Ver D-29.
CONFIG_PATH = caminho_do_config()
migrar_config_legado(CONFIG_PATH)


def carregar_config(caminho=CONFIG_PATH):
    """Mantido como nome público; a leitura em si mora em `core/config_store.py`."""
    return config_store.carregar(caminho)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    config = carregar_config()

    window = MainWindow(config, config_path=CONFIG_PATH)
    window.show()

    if not window.estado.onboarding_feito:
        from ui.onboarding import OnboardingDialog
        dialog = OnboardingDialog(window.estado, parent=window)
        dialog.exec()

    sys.exit(app.exec())