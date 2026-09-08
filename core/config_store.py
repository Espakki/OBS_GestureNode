"""Ler e gravar o `config.json`. Ver D-47.

A leitura estava em `main.py` e a escrita em `ui/mixins/config_mixin.py`. As duas metades
da mesma responsabilidade moravam em camadas diferentes, e nenhuma delas era acessível a
teste sem subir o app.

**A escrita é atômica** (D-22): grava num temporário no mesmo diretório e faz `os.replace`.
Escrever por cima do arquivo bom deixa uma janela em que uma queda de energia produz um
`config.json` truncado — e um JSON truncado não abre, ou seja, o usuário perde tudo. O
temporário precisa ser no mesmo diretório porque `os.replace` só é atômico dentro do
mesmo volume.
"""

import json
import os
import tempfile
from pathlib import Path

from util.logger import get_logger

logger = get_logger(__name__)


class FalhaAoSalvar(Exception):
    """Não foi possível gravar. Carrega o motivo original em `causa`."""

    def __init__(self, caminho, causa):
        super().__init__(f"não foi possível gravar em {caminho}: {causa}")
        self.caminho = caminho
        self.causa = causa


def carregar(caminho):
    """Devolve o config lido, ou `{}` quando não há arquivo utilizável.

    Todo caminho de falha devolve `{}` em vez de estourar: o app precisa abrir mesmo com
    config ausente ou corrompido — é o primeiro boot, e é também a única forma de o
    usuário conseguir reconfigurar depois de um arquivo quebrado.
    """
    caminho = Path(caminho)

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        logger.warning("Arquivo de configuração não encontrado: %s", caminho)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("JSON inválido em %s: %s", caminho, exc)
        return {}
    except OSError as exc:
        logger.error("Erro ao ler configuração %s: %s", caminho, exc)
        return {}

    if not isinstance(dados, dict):
        logger.error("Configuração em %s não é um objeto JSON; ignorando", caminho)
        return {}

    return dados


def salvar(config, caminho):
    """Grava atomicamente. Levanta `FalhaAoSalvar` quando não consegue."""
    caminho = Path(caminho)
    diretorio = caminho.parent

    try:
        descritor, temporario = tempfile.mkstemp(dir=str(diretorio), suffix=".tmp")
    except OSError as exc:
        logger.error("Falha ao criar temporário em %s: %s", diretorio, exc)
        raise FalhaAoSalvar(caminho, exc) from exc

    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(config, arquivo, indent=4, ensure_ascii=False)
        os.replace(temporario, str(caminho))
    except OSError as exc:
        _descartar(temporario)
        logger.error("Falha ao salvar configuração: %s", exc)
        raise FalhaAoSalvar(caminho, exc) from exc
    except Exception:
        _descartar(temporario)
        raise


def _descartar(temporario):
    try:
        os.unlink(temporario)
    except OSError:
        pass
