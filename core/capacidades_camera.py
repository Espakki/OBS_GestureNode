"""O que a câmera realmente aceita, perguntado ao DirectShow. Ver D-38.

Sem isto, o app descobre o que a câmera não suporta **falhando**: o `[Errno 5]` do
DirectShow é o mesmo para "dispositivo ocupado" e "modo não suportado" (D-32), então uma
webcam sem 60 fps produzia um erro que parecia disputa de dispositivo.

`pygrabber` enumera os formatos **sem abrir o dispositivo pelo FFmpeg** — medido em ~170ms
para listar dispositivos e enumerar formatos. Barato o bastante para perguntar toda vez que
a câmera selecionada muda, o que dispensa cache: cache de capacidade envelhece mal (trocar
de webcam com cache velho esconderia modos que funcionam) e aqui não é preciso.

**Fail-open por princípio:** se a consulta falhar ou vier vazia, `capacidades()` devolve
`{}` e quem chama deve oferecer tudo. Um probe quebrado não pode trancar o usuário fora
de opções que a câmera tem — o fallback de FPS do D-32 continua sendo a rede embaixo.
"""

from util.logger import get_logger

logger = get_logger(__name__)

# O app pede MJPEG em `core/camera.py`, então só os modos MJPEG importam.
_CODEC = "MJPG"


def _fps_maximo(formato):
    """Maior FPS do formato, tolerando os campos trocados do pygrabber.

    O pygrabber reporta `min_framerate=30, max_framerate=5` para um modo cujo range real
    é 5–30 — os nomes vêm invertidos, provavelmente porque o DirectShow expõe *intervalos*
    entre frames, e o menor intervalo é o maior FPS. Confiar no rótulo inverteria a lógica
    e filtraria exatamente ao contrário, então pegamos o maior dos dois.
    """
    valores = [
        formato.get("min_framerate", 0) or 0,
        formato.get("max_framerate", 0) or 0,
    ]
    return max(valores)


def capacidades(indice_dispositivo):
    """`{(largura, altura): fps_maximo}` para os modos MJPEG do dispositivo.

    Devolve `{}` quando não dá para saber — dispositivo inexistente, DirectShow indisponível
    ou nenhum modo MJPEG. Quem chama trata isso como "não filtre nada".
    """
    try:
        from pygrabber.dshow_graph import FilterGraph
    except Exception as exc:  # pragma: no cover - depende do ambiente
        logger.debug("pygrabber indisponível, sem filtro de capacidades: %s", exc)
        return {}

    try:
        grafo = FilterGraph()
        grafo.add_video_input_device(int(indice_dispositivo))
        formatos = grafo.get_input_device().get_formats()
    except Exception as exc:
        logger.warning(
            "Não foi possível consultar as capacidades da câmera %s: %s",
            indice_dispositivo, exc,
        )
        return {}

    modos = {}
    for formato in formatos or []:
        if _CODEC not in str(formato.get("media_type_str", "")).upper():
            continue

        largura = formato.get("width")
        altura = formato.get("height")
        if not largura or not altura:
            continue

        fps = _fps_maximo(formato)
        chave = (int(largura), int(altura))
        modos[chave] = max(modos.get(chave, 0), fps)

    if not modos:
        logger.info(
            "Câmera %s não reportou modos MJPEG; nenhum filtro será aplicado",
            indice_dispositivo,
        )

    return modos


def resolucao_suportada(modos, largura, altura):
    """Sem dados (`modos` vazio), tudo é considerado suportado — fail-open."""
    if not modos:
        return True
    return (int(largura), int(altura)) in modos


def fps_suportado(modos, largura, altura, fps):
    """Se a resolução não é conhecida, não bloqueia o FPS — quem barra é a resolução."""
    if not modos:
        return True

    maximo = modos.get((int(largura), int(altura)))
    if not maximo:
        return True

    return float(fps) <= float(maximo)


def fps_maximo_do_dispositivo(modos):
    """Maior FPS entre todas as resoluções. `None` quando não há dados."""
    if not modos:
        return None
    return max(modos.values())


# Acima disto, resolução não melhora detecção: o `HandTracker` reduz tudo para
# `PROCESS_W = 640` antes da inferência. Só vale subir quando a imagem também é entregue
# ao público, que é o caso do modo automático. Ver D-39.
RESOLUCAO_SEM_VCAM = (1280, 720)


def preset_recomendado(modos, modo, resolucoes, fps_possiveis):
    """Melhor `(largura, altura, fps)` para o modo de operação. `None` sem dados.

    "Melhor" **não é propriedade da câmera sozinha** — depende de para onde a imagem vai:

    - `teste` e `manual`: a captura só alimenta a inferência, que trabalha a 640px. Passar
      de 720p custa CPU e não melhora detecção em nada, então o alvo é 720p.
    - `automatico`: a imagem também vai para o OBS, ou seja, é o que o público vê. Aí a
      maior resolução suportada é a escolha certa.

    Pegar sempre a maior suportada — o palpite óbvio — estaria errado em dois dos três modos.

    `resolucoes` e `fps_possiveis` são o que a interface oferece: não adianta recomendar um
    modo que a câmera tem mas o app não expõe.
    """
    if not modos:
        return None

    suportadas = [
        (largura, altura)
        for largura, altura in resolucoes
        if resolucao_suportada(modos, largura, altura)
    ]
    if not suportadas:
        return None

    if modo == "automatico":
        escolhida = max(suportadas, key=lambda r: r[0] * r[1])
    else:
        limite = RESOLUCAO_SEM_VCAM[0] * RESOLUCAO_SEM_VCAM[1]
        ate_o_alvo = [r for r in suportadas if r[0] * r[1] <= limite]
        # Sem nenhuma opção até 720p, a menor suportada é a mais próxima da intenção.
        escolhida = (
            max(ate_o_alvo, key=lambda r: r[0] * r[1])
            if ate_o_alvo
            else min(suportadas, key=lambda r: r[0] * r[1])
        )

    largura, altura = escolhida
    validos = [f for f in fps_possiveis if fps_suportado(modos, largura, altura, f)]
    if not validos:
        return None

    return (largura, altura, max(validos))
