"""Implementação Linux: som por tocador externo, teclas por injetor externo. Ver D-46.

Diferente de `_windows.py`, este módulo **importa em qualquer sistema**: ele não toca em
API nativa, só monta linhas de comando e chama `subprocess`. Isso é de propósito — deixa a
lógica inteira (escolha de backend, mapa de teclas, montagem do comando) coberta por teste
automatizado rodando no Windows, que é a única máquina que este projeto tem.

**O que os testes NÃO provam:** que o comando montado funciona. Isso exige Linux real, e o
projeto já aprendeu que câmera e injeção de teclas só se provam no hardware. O que está
coberto é a forma do comando; o efeito dele, não.

**Por que backends externos e não uma lib.** No Linux não existe o equivalente do
`SendInput`: injetar tecla é privilégio do servidor gráfico. No X11 qualquer cliente pode
falar com o servidor (`xdotool`); no Wayland isso foi fechado por design, e sobra ou o
protocolo de teclado virtual (`wtype`, que GNOME e KDE não implementam) ou o `uinput` do
kernel (`ydotool`, que exige daemon e permissão). Não há um caminho único que cubra todo
mundo — daí a lista ordenada, e não uma escolha só.
"""

import os
import shutil
import subprocess

from plataforma import _generico
from util.logger import get_logger

logger = get_logger(__name__)

NOME = "Linux"

# O FFmpeg no Linux lê a webcam pelo v4l2, que endereça por nó, não por nome.
FORMATO_CAPTURA = "v4l2"

# Nenhum comando aqui é interativo; se algum travar, travou o gesto. O corte é curto de
# propósito: melhor perder um atalho do que segurar a thread de ações.
TIMEOUT_SEGUNDOS = 2.0


def url_do_dispositivo(nome_dispositivo, indice=0):
    """O v4l2 endereça por NÓ, não por nome — o oposto do DirectShow. Ver D-42."""
    return f"/dev/video{int(indice)}"


# --------------------------------------------------------------------------- áudio

# Ordem por família: os dois primeiros são o caminho normal de uma distro moderna
# (o PipeWire expõe `paplay` por compatibilidade com o PulseAudio), `aplay` é o ALSA cru.
_TOCADORES_WAV = (
    ("paplay", ()),
    ("aplay", ("-q",)),
    ("ffplay", ("-nodisp", "-autoexit", "-loglevel", "quiet")),
    ("play", ("-q",)),
)

# `paplay` e `aplay` só tocam PCM. Para qualquer outra extensão eles falhariam, então a
# ordem inverte: quem decodifica formato comprimido vem primeiro.
_TOCADORES_COMPRIMIDO = (
    ("ffplay", ("-nodisp", "-autoexit", "-loglevel", "quiet")),
    ("play", ("-q",)),
    ("paplay", ()),
)

# Processos de som ainda vivos. Sem isto viram zumbi: ninguém chama `wait()`, porque o
# `SND_ASYNC` do Windows que estamos imitando não deixa esperar.
_tocando = []


def _limpar_tocadores():
    """Recolhe o status de quem já terminou. Chamado a cada som novo."""
    global _tocando
    _tocando = [processo for processo in _tocando if processo.poll() is None]


def tocadores_para(caminho):
    """Candidatos a tocador, na ordem, conforme a extensão do arquivo."""
    extensao = os.path.splitext(str(caminho or ""))[1].lower()
    return _TOCADORES_WAV if extensao in (".wav", ".wave") else _TOCADORES_COMPRIMIDO


def tocar_som(caminho):
    """Toca sem bloquear, no primeiro tocador instalado que aceite o formato.

    Mesmo contrato do Windows: caminho vazio ou arquivo ausente é `False` com aviso, nunca
    exceção — um som que não toca não pode derrubar a ação que o disparou.
    """
    if not caminho:
        return False

    if not os.path.exists(caminho):
        logger.warning("Arquivo de som não encontrado: %s", caminho)
        return False

    _limpar_tocadores()

    candidatos = tocadores_para(caminho)
    for programa, argumentos in candidatos:
        executavel = shutil.which(programa)
        if executavel is None:
            continue

        try:
            processo = subprocess.Popen(
                [executavel, *argumentos, str(caminho)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            logger.warning("Falha ao iniciar %s: %s", programa, exc)
            continue

        _tocando.append(processo)
        return True

    logger.warning(
        "Nenhum tocador de áudio encontrado (%s); som ignorado: %s",
        ", ".join(nome for nome, _ in candidatos),
        caminho,
    )
    return False


# --------------------------------------------------------------------------- teclado

# Nomes de keysym do X11, que `xdotool` e `wtype` compartilham. As chaves são exatamente
# os tokens que `actions/action_manager.py` produz — inclusive os de duas palavras.
KEYSYMS = {
    "enter": "Return",
    "tab": "Tab",
    "space": "space",
    "esc": "Escape",
    "backspace": "BackSpace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page up": "Prior",
    "page down": "Next",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "menu": "Menu",
    "help": "Help",
    "pause": "Pause",
    "print screen": "Print",
    "scroll lock": "Scroll_Lock",
    "caps lock": "Caps_Lock",
    "num lock": "Num_Lock",
    "/": "slash",
    "\\": "backslash",
    ",": "comma",
    ".": "period",
    ";": "semicolon",
    "'": "apostrophe",
    "[": "bracketleft",
    "]": "bracketright",
    "`": "grave",
    "-": "minus",
    "=": "equal",
    "+": "plus",
}

# `xdotool` fala "super"; `wtype` fala "logo". Mesma tecla, nomes diferentes.
MODS_XDOTOOL = {"ctrl": "ctrl", "alt": "alt", "shift": "shift", "windows": "super"}
MODS_WTYPE = {"ctrl": "ctrl", "alt": "alt", "shift": "shift", "windows": "logo"}

# Códigos de `linux/input-event-codes.h`. O `ydotool` moderno não aceita nome de tecla:
# ele escreve direto no `uinput`, que só conhece número.
KEYCODES = {
    "esc": 1, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9,
    "9": 10, "0": 11, "-": 12, "=": 13, "backspace": 14, "tab": 15,
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20, "y": 21, "u": 22, "i": 23,
    "o": 24, "p": 25, "[": 26, "]": 27, "enter": 28,
    "a": 30, "s": 31, "d": 32, "f": 33, "g": 34, "h": 35, "j": 36, "k": 37,
    "l": 38, ";": 39, "'": 40, "`": 41, "\\": 43,
    "z": 44, "x": 45, "c": 46, "v": 47, "b": 48, "n": 49, "m": 50,
    ",": 51, ".": 52, "/": 53, "space": 57, "caps lock": 58,
    "num lock": 69, "scroll lock": 70,
    "print screen": 99, "home": 102, "up": 103, "page up": 104, "left": 105,
    "right": 106, "end": 107, "down": 108, "page down": 109, "insert": 110,
    "delete": 111, "pause": 119, "menu": 127, "help": 138,
}

# O "+" do app é a mesma tecla física do "=", como no Windows: lá os dois viram VK 0xBB.
KEYCODES["+"] = KEYCODES["="]

KEYCODES_MODS = {"ctrl": 29, "shift": 42, "alt": 56, "windows": 125}

# As teclas de função não são contíguas no header do kernel: F1–F10 ficam juntas, F11 e
# F12 caem depois do bloco de numérico, e F13–F24 moram numa faixa bem mais alta.
_KEY_F1 = 59
_KEY_F11 = 87
_KEY_F13 = 183


def _numero_de_f(token):
    """`"f5"` → 5. Devolve `None` para o que não for tecla de função."""
    texto = str(token or "").lower().strip()
    if not (texto.startswith("f") and texto[1:].isdigit()):
        return None
    numero = int(texto[1:])
    return numero if 1 <= numero <= 24 else None


def token_para_keysym(token):
    """Converte um token do app no nome de keysym do X11."""
    token = str(token or "").lower().strip()
    if not token:
        return None

    if len(token) == 1 and token.isalnum():
        return token

    fn = _numero_de_f(token)
    if fn is not None:
        return f"F{fn}"

    return KEYSYMS.get(token)


def token_para_keycode(token):
    """Converte um token do app no código de tecla do kernel."""
    token = str(token or "").lower().strip()
    if not token:
        return None

    fn = _numero_de_f(token)
    if fn is not None:
        if fn <= 10:
            return _KEY_F1 + (fn - 1)
        if fn <= 12:
            return _KEY_F11 + (fn - 11)
        return _KEY_F13 + (fn - 13)

    return KEYCODES.get(token)


def comando_xdotool(mods, tecla):
    """`xdotool key ctrl+shift+F5` — a combinação inteira num argumento só."""
    keysym = token_para_keysym(tecla)
    if keysym is None:
        return None

    partes = [MODS_XDOTOOL[m] for m in mods if m in MODS_XDOTOOL]
    return ["xdotool", "key", "+".join(partes + [keysym])]


def comando_wtype(mods, tecla):
    """`wtype -M ctrl -k F5 -m ctrl` — segura, bate, e solta na ordem inversa.

    Soltar explicitamente não é zelo: o `wtype` não desfaz sozinho o que o `-M` segurou, e
    um modificador preso contamina tudo o que o usuário digitar depois.
    """
    keysym = token_para_keysym(tecla)
    if keysym is None:
        return None

    aplicaveis = [m for m in mods if m in MODS_WTYPE]

    comando = ["wtype"]
    for mod in aplicaveis:
        comando += ["-M", MODS_WTYPE[mod]]
    comando += ["-k", keysym]
    for mod in reversed(aplicaveis):
        comando += ["-m", MODS_WTYPE[mod]]
    return comando


def comando_ydotool(mods, tecla):
    """`ydotool key 29:1 63:1 63:0 29:0` — cada evento explícito, `código:pressionado`."""
    codigo = token_para_keycode(tecla)
    if codigo is None:
        return None

    aplicaveis = [m for m in mods if m in KEYCODES_MODS]

    eventos = [f"{KEYCODES_MODS[m]}:1" for m in aplicaveis]
    eventos.append(f"{codigo}:1")
    eventos.append(f"{codigo}:0")
    eventos += [f"{KEYCODES_MODS[m]}:0" for m in reversed(aplicaveis)]
    return ["ydotool", "key", *eventos]


BACKENDS = {
    "xdotool": comando_xdotool,
    "wtype": comando_wtype,
    "ydotool": comando_ydotool,
}


def sessao_grafica():
    """`"wayland"`, `"x11"` ou `"desconhecida"`.

    `XDG_SESSION_TYPE` é a resposta direta quando existe. As variáveis de display são o
    plano B: um ambiente que não a define ainda se revela por elas.
    """
    tipo = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if tipo in ("wayland", "x11"):
        return tipo

    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "desconhecida"


def backends_preferidos(sessao=None):
    """Ordem de tentativa dos injetores, do menos custoso ao mais.

    `xdotool` e `wtype` falam com o servidor gráfico e não pedem nada do usuário.
    `ydotool` vem por último em toda ordem porque escreve no `uinput`: exige daemon rodando
    e permissão no dispositivo — mas é o único que funciona no Wayland do GNOME e do KDE,
    que não implementam o protocolo de teclado virtual do qual o `wtype` depende.
    """
    if sessao is None:
        sessao = sessao_grafica()

    if sessao == "x11":
        return ["xdotool", "ydotool"]
    if sessao == "wayland":
        return ["wtype", "ydotool"]
    return ["xdotool", "wtype", "ydotool"]


def _executar(comando):
    """Roda o injetor. `True` só com saída 0 — qualquer outra coisa é tentar o próximo."""
    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_SEGUNDOS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("%s não respondeu em %ss", comando[0], TIMEOUT_SEGUNDOS)
        return False
    except OSError as exc:
        logger.warning("Falha ao executar %s: %s", comando[0], exc)
        return False

    if resultado.returncode == 0:
        return True

    erro = (resultado.stderr or b"").decode("utf-8", "replace").strip()
    logger.warning("%s saiu com %s: %s", comando[0], resultado.returncode, erro)
    return False


def enviar_atalho(mods, tecla):
    """Tenta os injetores da sessão em ordem; o pacote `keyboard` é a última rede.

    Um backend instalado que falha não encerra a tentativa: no Wayland do GNOME o `wtype`
    existe e sai com erro, porque o compositor não implementa o protocolo — é exatamente o
    caso em que o `ydotool` seguinte resolve.
    """
    tentados = []

    for nome_backend in backends_preferidos():
        executavel = shutil.which(nome_backend)
        if executavel is None:
            continue

        comando = BACKENDS[nome_backend](mods, tecla)
        if comando is None:
            logger.warning("%s não sabe representar a tecla '%s'", nome_backend, tecla)
            continue

        tentados.append(nome_backend)
        if _executar([executavel, *comando[1:]]):
            return True

    if not tentados:
        logger.warning(
            "Nenhum injetor de teclas instalado (%s); tentando o pacote `keyboard`. "
            "Instale um deles para não depender de root.",
            ", ".join(backends_preferidos()),
        )

    # O `keyboard` exige root no Linux, então é rede e não estratégia — mas um caminho
    # improvável ainda é melhor que nenhum. Ver `_generico`.
    return _generico.enviar_atalho(mods, tecla)
