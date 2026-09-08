"""Versão e licenças, para a aba Sobre. Ver D-51.

Lê o catálogo que `ferramentas/coletar_licencas.py` gerou. Se ele não existir, a aba diz
isso em vez de mostrar uma lista vazia — um catálogo ausente é obrigação de distribuição
não cumprida, não um detalhe cosmético.
"""

import re
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from util.logger import get_logger
from version import NOME_DO_APP, REPOSITORIO, __version__

logger = get_logger(__name__)

# Uma linha da tabela do LEIA-ME.md: | nome | versão | licença |
_LINHA = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def diretorio_de_licencas():
    """Onde as licenças ficam, rodando do código ou empacotado.

    Congelado, o PyInstaller extrai os dados para `sys._MEIPASS`; do código-fonte elas
    estão ao lado da raiz do projeto. Ver D-29 para o mesmo problema no config.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "licencas"
    return Path(__file__).resolve().parent.parent.parent / "licencas"


class PonteSobre(QObject):

    mudou = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dependencias = self._ler_catalogo()

    def _ler_catalogo(self):
        catalogo = diretorio_de_licencas() / "LEIA-ME.md"
        if not catalogo.is_file():
            logger.warning("Catálogo de licenças ausente: %s", catalogo)
            return []

        linhas = []
        try:
            for linha in catalogo.read_text(encoding="utf-8").splitlines():
                achado = _LINHA.match(linha.strip())
                if not achado:
                    continue
                nome, versao, licenca = (g.strip() for g in achado.groups())
                # Pula o cabeçalho e o separador da tabela markdown.
                if nome.lower() == "biblioteca" or set(nome) <= {"-", ":"}:
                    continue
                linhas.append({"nome": nome, "versao": versao, "licenca": licenca})
        except OSError as exc:
            logger.error("Falha ao ler o catálogo de licenças: %s", exc)
            return []

        return linhas

    @Property(str, notify=mudou)
    def nome(self):
        return NOME_DO_APP

    @Property(str, notify=mudou)
    def versao(self):
        return __version__

    @Property(str, notify=mudou)
    def urlDoRepositorio(self):
        return f"https://github.com/{REPOSITORIO}"

    @Property(list, notify=mudou)
    def dependencias(self):
        return list(self._dependencias)

    @Property(bool, notify=mudou)
    def temLicencas(self):
        return diretorio_de_licencas().is_dir()

    @Slot()
    def abrirLicencas(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(diretorio_de_licencas())))

    @Slot(str)
    def abrirLink(self, url):
        QDesktopServices.openUrl(QUrl(url))
