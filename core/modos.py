"""Modo de operação do app — fonte única de verdade.

Mesmo padrão de `gesture_aliases.py`: um módulo pequeno e sem dependências, importado por
quem precisar, para que não existam duas regras divergentes. Ver D-18 e D-27.

Os três modos (D-15, D-16, D-17):
- `teste`      — detecta gestos mas bloqueia TODAS as ações. Sandbox de calibração.
- `manual`     — conecta no OBS e executa ações. Sem câmera virtual.
- `automatico` — padrão de fábrica. Igual ao manual, mais a câmera virtual.
"""

MODOS_VALIDOS = frozenset({"teste", "manual", "automatico"})

MODO_PADRAO = "automatico"

# Valores da v1.1 que ainda podem aparecer em configs antigas.
_LEGADO = {"test": "teste", "obs": "automatico"}


def migrar_modo(bruto):
    """Normaliza qualquer valor de `modo` para um dos três canônicos.

    Aceita valor legado, maiúsculas e espaço em volta. Qualquer coisa que não case —
    incluindo None, string vazia ou tipo inesperado — vira `automatico`, porque um modo
    inválido não pode impedir o app de subir.
    """
    texto = str(bruto or MODO_PADRAO).strip().lower()
    texto = _LEGADO.get(texto, texto)
    return texto if texto in MODOS_VALIDOS else MODO_PADRAO
