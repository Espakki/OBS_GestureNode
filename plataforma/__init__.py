"""Tudo que depende do sistema operacional mora atrás desta fronteira. Ver D-42.

**O nome é `plataforma`, não `platform`, de propósito:** `platform` é módulo da stdlib e
um pacote com esse nome o sombrearia — inclusive para bibliotecas de terceiros que o
importam. Também segue a convenção do projeto: domínio em português.

O que motiva existir: `actions/action_manager.py` fazia `import winsound` no topo. Como a
cadeia `main.py → ui → engine → action_manager` é toda import de nível de módulo, isso
derrubava o app em qualquer sistema que não fosse Windows **antes de a janela abrir**. O
arquivo específico de uma plataforma existir no disco de outra é inofensivo; o `import`
executar é que é fatal.

A escolha acontece uma vez, aqui, olhando `sys.platform`. Cada implementação só é
importada no sistema dela — `_windows` nunca é carregado no Linux e vice-versa.

Windows e Linux têm implementação própria; o resto cai no `_generico`. Para portar para
um sistema novo, criar o módulo e adicioná-lo ao `_escolher` — nada fora deste pacote
precisa saber que ele existe.
"""

import sys

from util.logger import get_logger

logger = get_logger(__name__)


def _escolher():
    if sys.platform.startswith("win"):
        from plataforma import _windows

        return _windows

    if sys.platform.startswith("linux"):
        from plataforma import _linux

        return _linux

    # Ainda não há implementação nativa para este sistema. O `_generico` cobre teclado
    # via pacote `keyboard` e recusa áudio com aviso, em vez de derrubar o app.
    from plataforma import _generico

    logger.warning(
        "Sem implementação nativa para %s; usando o backend genérico. "
        "Áudio indisponível e hotkeys podem exigir privilégio elevado.",
        sys.platform,
    )
    return _generico


_impl = _escolher()


def nome():
    """Nome legível da plataforma ativa, para log e diagnóstico."""
    return _impl.NOME


def tocar_som(caminho):
    """Toca um arquivo de áudio sem bloquear. Devolve `True` se conseguiu."""
    return _impl.tocar_som(caminho)


def enviar_atalho(mods, tecla):
    """Injeta uma combinação já normalizada. `mods` como ["ctrl", "shift"].

    Quem chama é responsável por validar e normalizar o texto — isso é parsing, não
    plataforma, e continua em `actions/action_manager.py`.
    """
    return _impl.enviar_atalho(mods, tecla)


def formato_de_captura():
    """Formato de entrada do FFmpeg/PyAV: `dshow` no Windows, `v4l2` no Linux."""
    return _impl.FORMATO_CAPTURA


def url_do_dispositivo(nome_dispositivo, indice=0):
    """Como o FFmpeg endereça a câmera nesta plataforma.

    Windows usa `video=<nome>`; Linux usa `/dev/video<indice>`. A diferença não é só de
    sintaxe — é de identidade: um usa nome, o outro usa número.
    """
    return _impl.url_do_dispositivo(nome_dispositivo, indice)
