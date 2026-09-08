"""Traduzir um evento de tecla no texto de atalho. Ver D-50.

Isto morava dentro do `HotkeyLineEdit`, em `ui/tabs/gestos_tab.py`. Saiu de lá por um
motivo concreto: com a aba Gestos em QML, a captura passa a existir em **dois** lugares, e
uma regra duplicada é uma regra que vai divergir.

**O que está em jogo não é organização.** A proteção contra AltGr (commit `8838edf`) vive
aqui. Em layouts como o ABNT2, Ctrl+Alt funciona como AltGr e o Qt entrega o **caractere
composto** no texto do evento — `æ` no lugar de `z`. Gravar isso produziria um atalho que
nunca casa com o registrado no OBS, e o usuário ficaria com um gesto que não faz nada, sem
mensagem de erro nenhuma.

A defesa é usar o **código** da tecla, nunca o texto digitado. Se a captura em QML fosse
escrita do zero, esse cuidado se perderia — e o teste continuaria verde, porque estaria
exercitando o widget antigo.

O módulo não importa nada de UI além dos enums do Qt: recebe números e devolve texto.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

MODIFICADORES = (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta)

# A ordem é fixa para que a mesma combinação produza sempre o mesmo texto — o config é
# comparado como string, e "Shift+Ctrl+A" nunca casaria com "Ctrl+Shift+A".
_ORDEM = (
    (Qt.Key_Control, Qt.ControlModifier, "Ctrl"),
    (Qt.Key_Alt, Qt.AltModifier, "Alt"),
    (Qt.Key_Shift, Qt.ShiftModifier, "Shift"),
    (Qt.Key_Meta, Qt.MetaModifier, "Win"),
)

NOME_POR_CODIGO = {
    Qt.Key_Space: "Space",
    Qt.Key_Tab: "Tab",
    Qt.Key_Backtab: "Tab",
    Qt.Key_Return: "Enter",
    Qt.Key_Enter: "Enter",
    Qt.Key_Backspace: "Backspace",
    Qt.Key_Delete: "Delete",
    Qt.Key_Insert: "Insert",
    Qt.Key_Home: "Home",
    Qt.Key_End: "End",
    Qt.Key_PageUp: "PageUp",
    Qt.Key_PageDown: "PageDown",
    Qt.Key_Left: "Left",
    Qt.Key_Right: "Right",
    Qt.Key_Up: "Up",
    Qt.Key_Down: "Down",
    Qt.Key_Escape: "Esc",
    Qt.Key_Pause: "Pause",
    Qt.Key_Print: "PrintScreen",
    Qt.Key_ScrollLock: "ScrollLock",
    Qt.Key_CapsLock: "CapsLock",
    Qt.Key_NumLock: "NumLock",
    Qt.Key_Menu: "Menu",
    Qt.Key_Help: "Help",
}

PONTUACAO_POR_CODIGO = {
    Qt.Key_Plus: "Plus",
    Qt.Key_Minus: "-",
    Qt.Key_Equal: "=",
    Qt.Key_Slash: "/",
    Qt.Key_Backslash: "\\",
    Qt.Key_Comma: ",",
    Qt.Key_Period: ".",
    Qt.Key_Semicolon: ";",
    Qt.Key_Apostrophe: "'",
    Qt.Key_BracketLeft: "[",
    Qt.Key_BracketRight: "]",
    Qt.Key_QuoteLeft: "`",
}

_PERMITIDOS = {
    "Space", "Tab", "Enter", "Return", "Backspace", "Delete",
    "Insert", "Home", "End", "PageUp", "PageDown", "Up", "Down",
    "Left", "Right",
}


def modificadores_de_flags(flags):
    """Os modificadores presentes nas flags do evento, na ordem canônica."""
    return [nome for _, flag, nome in _ORDEM if flags & flag]


def modificadores_de_teclas(codigos_pressionados):
    """Idem, a partir das teclas que estão fisicamente seguradas.

    Existe além da versão por flags porque enquanto o usuário só segura Ctrl+Shift, sem ter
    batido a tecla final, as flags do evento ainda não refletem o que está seguro — e é
    disso que sai o texto "Ctrl+Shift+..." mostrado durante a captura.
    """
    return [nome for codigo, _, nome in _ORDEM if codigo in codigos_pressionados]


def _do_virtual_key_nativo(native_vk):
    """A tecla FÍSICA, conforme o sistema. É esta a defesa contra o AltGr.

    Em layout ABNT2, Ctrl+Alt vira AltGr e o Qt entrega `æ` no texto; o virtual key nativo
    continua dizendo `Z`, que é a tecla que o usuário de fato apertou.
    """
    try:
        native_vk = int(native_vk)
    except (TypeError, ValueError):
        return ""

    if 0x41 <= native_vk <= 0x5A:  # A-Z
        return chr(native_vk)
    if 0x30 <= native_vk <= 0x39:  # 0-9
        return chr(native_vk)
    if 0x70 <= native_vk <= 0x87:  # F1-F24
        return f"F{native_vk - 0x6F}"
    return ""


def nome_da_tecla(codigo, flags=0, texto="", native_vk=0):
    """O nome canônico da tecla final, ou `""` se ela não serve como atalho."""
    if Qt.Key_A <= codigo <= Qt.Key_Z:
        return chr(codigo)

    if Qt.Key_0 <= codigo <= Qt.Key_9:
        return chr(codigo)

    nativo = _do_virtual_key_nativo(native_vk)
    if nativo:
        return nativo

    if Qt.Key_F1 <= codigo <= Qt.Key_F24:
        return f"F{codigo - Qt.Key_F1 + 1}"

    if codigo in NOME_POR_CODIGO:
        return NOME_POR_CODIGO[codigo]

    if codigo in PONTUACAO_POR_CODIGO:
        return PONTUACAO_POR_CODIGO[codigo]

    normalizado = QKeySequence(codigo).toString(QKeySequence.NativeText).strip()
    if not normalizado:
        return ""

    # Descarta caractere de layout/AltGr (©åéßæ) mas mantém pontuação ASCII.
    if len(normalizado) == 1 and not normalizado.isascii():
        return ""

    if normalizado == "+":
        return "Plus"
    if normalizado.startswith("F") and normalizado[1:].isdigit():
        return normalizado.upper()
    if normalizado in _PERMITIDOS:
        return normalizado
    if len(normalizado) == 1 and normalizado.isascii():
        return normalizado.upper()
    return ""


def montar(codigo, flags=0, texto="", native_vk=0, segurados=()):
    """O atalho completo, ou `""` quando a combinação não serve.

    Sem modificador não há atalho: uma tecla solta viraria um gesto que dispara toda vez
    que o usuário digitasse aquela letra em qualquer lugar.
    """
    if codigo in MODIFICADORES:
        return ""

    mods = modificadores_de_flags(flags) or modificadores_de_teclas(segurados)
    if not mods:
        return ""

    tecla = nome_da_tecla(codigo, flags, texto, native_vk)
    if not tecla:
        # Último recurso: um ASCII de um caractere no texto do evento. Só chega aqui quando
        # nem o código nem o virtual key nativo disseram algo utilizável.
        limpo = (texto or "").strip()
        if len(limpo) == 1 and limpo.isascii():
            tecla = limpo.upper()

    if not tecla:
        return ""

    return "+".join(mods + [tecla])


def montar_de_evento(evento, segurados=()):
    """Conveniência para quem tem um `QKeyEvent` em mãos."""
    return montar(
        evento.key(),
        evento.modifiers(),
        evento.text(),
        evento.nativeVirtualKey(),
        segurados,
    )
