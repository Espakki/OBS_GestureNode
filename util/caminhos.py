"""Onde o `config.json` mora, dependendo de como o app foi iniciado.

Rodando do código-fonte, fica ao lado do `main.py` — conveniente para desenvolver e é o
comportamento histórico. Empacotado com PyInstaller, vai para `%APPDATA%`, porque
`Path(__file__).parent` no bundle congelado resolve para o `_MEIPASS`, ou seja
`dist\\main\\_internal\\` — dentro das entranhas do bundle. Isso funciona numa pasta de
usuário, mas instalado em `C:\\Program Files\\` o diretório não é gravável e o save falha.
Ver D-29 e B-08.
"""

import os
import shutil
import sys
from pathlib import Path

from util.logger import get_logger

logger = get_logger(__name__)

NOME_DO_APP = "OBS GestureNode"
NOME_DO_ARQUIVO = "config.json"


def esta_congelado():
    """True quando rodando a partir do executável do PyInstaller."""
    return getattr(sys, "frozen", False)


def _raiz_do_projeto():
    # util/caminhos.py -> util/ -> raiz
    return Path(__file__).resolve().parent.parent


def diretorio_do_config():
    """Diretório onde o config deve ser lido e gravado."""
    if not esta_congelado():
        return _raiz_do_projeto()

    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / NOME_DO_APP

    # Sem APPDATA (ambiente atípico), a home do usuário é gravável e serve.
    return Path.home() / f".{NOME_DO_APP.lower().replace(' ', '-')}"


def caminho_do_config(criar_diretorio=True):
    """Caminho completo do `config.json`, criando o diretório se necessário.

    `criar_diretorio=False` serve para consultar o caminho sem efeito colateral.
    """
    diretorio = diretorio_do_config()

    if criar_diretorio and esta_congelado():
        try:
            diretorio.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Não foi possível criar %s: %s", diretorio, exc)

    return diretorio / NOME_DO_ARQUIVO


def migrar_config_legado(destino):
    """Traz um config que tenha ficado no local antigo, dentro do bundle.

    Versões anteriores gravavam em `_MEIPASS/config.json`. Quem já usava o `.exe` tem as
    configurações lá; sem isto, atualizar o app faria o usuário perder tudo em silêncio.

    Só copia se o destino ainda não existir — nunca sobrescreve config atual.
    """
    if not esta_congelado() or destino.exists():
        return False

    legado = Path(getattr(sys, "_MEIPASS", "")) / NOME_DO_ARQUIVO
    if not legado.is_file():
        return False

    try:
        shutil.copy2(legado, destino)
        logger.info("Config migrado de %s para %s", legado, destino)
        return True
    except OSError as exc:
        logger.error("Falha ao migrar config de %s: %s", legado, exc)
        return False
