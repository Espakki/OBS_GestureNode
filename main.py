import sys
import json
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from util.logger import get_logger


logger = get_logger(__name__)


def carregar_config(caminho="config.json"):
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

    config = carregar_config()

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())