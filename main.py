"""OBS GestureNode — controle o OBS Studio por gestos de mão via webcam.

Copyright (C) 2026 Winicius Passaia

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo sob os termos da
Licença Pública Geral GNU, versão 3, publicada pela Free Software Foundation.

Distribuído na esperança de ser útil, mas SEM NENHUMA GARANTIA — sem sequer a garantia
implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM PROPÓSITO ESPECÍFICO. Veja a Licença
Pública Geral GNU para mais detalhes: <https://www.gnu.org/licenses/>.
"""

import sys
import json
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET
from util.caminhos import caminho_do_config, migrar_config_legado
from util.logger import get_logger


logger = get_logger(__name__)

# Empacotado, isto resolve para %APPDATA% em vez de _internal/ dentro do bundle. Ver D-29.
CONFIG_PATH = caminho_do_config()
migrar_config_legado(CONFIG_PATH)


def carregar_config(caminho=CONFIG_PATH):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        logger.warning("Arquivo de configuração não encontrado: %s", caminho)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("JSON inválido em %s: %s", caminho, exc)
        return {}
    except OSError as exc:
        logger.error("Erro ao ler configuração %s: %s", caminho, exc)
        return {}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    config = carregar_config()

    window = MainWindow(config, config_path=CONFIG_PATH)
    window.show()

    if not config.get("onboarding_done", False):
        from ui.onboarding import OnboardingDialog
        dialog = OnboardingDialog(config, window.salvar_config_automatico, parent=window)
        dialog.exec()

    sys.exit(app.exec())