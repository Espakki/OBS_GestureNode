"""Schema, defaults e migração do `config.json`. Ver D-47.

Isto morava em `ui/mixins/config_mixin.py::_init_config_schema`, dentro da janela. Era
regra de domínio na camada de apresentação: nada aqui precisa de widget, e a prova é que
o módulo inteiro não importa Qt.

**Por que sair da UI importa mais do que organização.** Enquanto estava lá, esta lógica só
rodava se alguém abrisse a `MainWindow` — ou seja, nunca em teste. As regras de clamp do
`hold_time` e do `cooldown` chegaram a existir em três lugares (aqui, no `select_gesture` e
no range do spinbox), e ninguém tinha como notar que divergiram.

`normalizar()` é pura: recebe config, devolve config. Não lê arquivo, não toca em tela.
"""

from core.gesture_aliases import GESTURE_ALIASES
from core.modos import migrar_modo

# Pisos de segurança. Abaixo disto o gesto dispara antes de o usuário terminar de fazê-lo,
# ou repete em rajada — os dois viram ação indesejada no meio de uma live.
HOLD_MINIMO = 0.5
COOLDOWN_MINIMO = 2.0

HOLD_PADRAO = 2.0
COOLDOWN_PADRAO = 2.0

# Campos que já existiram no config e hoje ninguém lê. Ficam listados, e não apenas
# apagados em silêncio, para que um leitor futuro saiba que a ausência é deliberada.
CAMPOS_APOSENTADOS_CAMERA = ("virtual_cam_mode", "vcam_device")  # D-11
CAMPOS_APOSENTADOS_RAIZ = ("combined_bindings",)  # D-31

PADROES_CAMERA = {
    "index": 0,
    "device_name": "",
    "width": 1280,
    "height": 720,
    "fps": 30,
    "process_fps": 30,
    "enable_virtual_camera": False,
    "virtual_camera_device": None,
    "show_skeleton": True,
    "skeleton_na_vcam": False,
}

PADROES_OBS = {
    "host": "localhost",
    "port": 4455,
    "password": "",
}


def binding_vazio(hold=HOLD_PADRAO, cooldown=COOLDOWN_PADRAO):
    """Um binding recém-criado, com todas as ações desligadas."""
    return {
        "enabled": True,
        "hold_time": hold,
        "cooldown": cooldown,
        "scene": "",
        "play_sound": False,
        "sound_file": "",
        "hotkey": "",
        "use_scene": False,
        "use_sound": False,
        "use_hotkey": False,
    }


def _limpar_campos_aposentados(config):
    camera = config.get("camera")
    if isinstance(camera, dict):
        for campo in CAMPOS_APOSENTADOS_CAMERA:
            camera.pop(campo, None)

    for campo in CAMPOS_APOSENTADOS_RAIZ:
        config.pop(campo, None)


def _aplicar_padroes(config):
    config.setdefault("max_maos", 1)
    config.setdefault("onboarding_done", False)

    camera = config.setdefault("camera", {})
    for chave, valor in PADROES_CAMERA.items():
        camera.setdefault(chave, valor)

    obs = config.setdefault("obs", {})
    for chave, valor in PADROES_OBS.items():
        obs.setdefault(chave, valor)


def _resolver_defaults_de_gesto(gestures_cfg):
    """Os nomes `hold_time`/`cooldown` sem prefixo são de uma versão antiga do config."""
    hold = gestures_cfg.get("default_hold_time", gestures_cfg.get("hold_time", HOLD_PADRAO))
    cooldown = gestures_cfg.get(
        "default_cooldown", gestures_cfg.get("cooldown", COOLDOWN_PADRAO)
    )

    gestures_cfg["default_hold_time"] = max(HOLD_MINIMO, float(hold))
    gestures_cfg["default_cooldown"] = max(COOLDOWN_MINIMO, float(cooldown))
    return gestures_cfg["default_hold_time"], gestures_cfg["default_cooldown"]


def _traduzir_aliases(mapa):
    """Converte chaves em código interno (`THUMBS_UP`) para nome de exibição."""
    if not isinstance(mapa, dict):
        return {}
    return {GESTURE_ALIASES.get(chave, chave): valor for chave, valor in mapa.items()}


def _resolver_gestos_ativos(gestures_cfg, bindings, gestos_validos):
    """Quais gestos aparecem na tela principal.

    Sem lista explícita, deduz dos bindings marcados como habilitados — é o caminho de
    quem vem de um config antigo, que não tinha `active_gestures`.
    """
    ativos = gestures_cfg.get("active_gestures")

    if not isinstance(ativos, list) or not ativos:
        ativos = [
            gesto
            for gesto, cfg in bindings.items()
            if isinstance(cfg, dict) and cfg.get("enabled", True)
        ]

    ativos = [gesto for gesto in ativos if gesto in gestos_validos]

    # Zero gestos ativos deixaria a tela principal vazia e o app sem nada para fazer.
    return ativos or [gestos_validos[0]]


def _normalizar_binding(bruto, gesto, ativos, hold_padrao, cooldown_padrao, cenas):
    if not isinstance(bruto, dict):
        bruto = {}

    cena = str(bruto.get("scene", cenas.get(gesto, ""))).strip()
    toca_som = bool(bruto.get("play_sound", False))
    atalho = str(bruto.get("hotkey", "")).strip()

    return {
        "enabled": bool(bruto.get("enabled", gesto in ativos)),
        "hold_time": max(HOLD_MINIMO, float(bruto.get("hold_time", hold_padrao))),
        "cooldown": max(COOLDOWN_MINIMO, float(bruto.get("cooldown", cooldown_padrao))),
        "scene": cena,
        "play_sound": toca_som,
        "sound_file": str(bruto.get("sound_file", "")).strip(),
        "hotkey": atalho,
        # `use_*` são mais novos que os campos que eles ligam. Num config anterior a eles,
        # ter valor preenchido é a única evidência de que a ação estava em uso.
        "use_scene": bool(bruto.get("use_scene", bool(cena))),
        "use_sound": bool(bruto.get("use_sound", toca_som)),
        "use_hotkey": bool(bruto.get("use_hotkey", bool(atalho))),
    }


def sincronizar_mapa_de_cenas(gestures_cfg):
    """Reconstrói `scene_map` a partir dos bindings, que são a fonte da verdade.

    O `scene_map` é redundante e existe porque a engine o consome direto. Derivar em vez
    de manter os dois à mão evita que discordem.
    """
    bindings = gestures_cfg.setdefault("bindings", {})
    gestures_cfg["scene_map"] = {
        gesto: cfg.get("scene", "")
        for gesto, cfg in bindings.items()
        if isinstance(cfg, dict) and cfg.get("scene", "")
    }
    return gestures_cfg["scene_map"]


def normalizar(config, gestos_validos):
    """Deixa o config completo e coerente. Muta e devolve o mesmo dicionário.

    `gestos_validos` é a lista de nomes de exibição que o app conhece. Ela é parâmetro, e
    não constante daqui, porque quem define o catálogo é a camada que também tem o ícone
    de cada gesto — isso é apresentação, não domínio.
    """
    if not isinstance(config, dict):
        config = {}
    if not gestos_validos:
        raise ValueError("gestos_validos não pode ser vazio")

    config["modo"] = migrar_modo(config.get("modo"))

    _limpar_campos_aposentados(config)
    _aplicar_padroes(config)

    gestures_cfg = config.setdefault("gestures", {})
    hold_padrao, cooldown_padrao = _resolver_defaults_de_gesto(gestures_cfg)

    cenas = _traduzir_aliases(gestures_cfg.get("scene_map", {}) or {})
    bindings = _traduzir_aliases(gestures_cfg.get("bindings", {}) or {})

    ativos = _resolver_gestos_ativos(gestures_cfg, bindings, gestos_validos)
    gestures_cfg["active_gestures"] = ativos

    gestures_cfg["bindings"] = {
        gesto: _normalizar_binding(
            bindings.get(gesto), gesto, ativos, hold_padrao, cooldown_padrao, cenas
        )
        for gesto in gestos_validos
    }

    sincronizar_mapa_de_cenas(gestures_cfg)
    return config
