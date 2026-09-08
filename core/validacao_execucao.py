"""A config está pronta para a engine subir? Ver D-47.

Isto morava em `ui/mixins/engine_mixin.py::_validar_config_execucao`, e é o exemplo mais
puro do que não tinha por que estar na UI: sessenta linhas sem uma única referência a
widget, decidindo uma questão de domínio.

**Erro x aviso.** Erro impede subir — a configuração produziria falha ou não faria nada
útil. Aviso deixa subir depois de confirmação: é algo suspeito que pode ser intencional,
como um gesto ativo sem ação, que acontece enquanto o usuário ainda está configurando.
"""

import os

# No modo teste nada é despachado (D-16), então nem OBS nem ação precisam estar válidos.
MODOS_QUE_USAM_OBS = ("manual", "automatico")


def _validar_obs(obs_cfg):
    erros = []

    if not str(obs_cfg.get("host", "")).strip():
        erros.append("Host do OBS está vazio")

    try:
        porta = int(obs_cfg.get("port", 0) or 0)
    except (TypeError, ValueError):
        porta = 0

    if porta <= 0:
        erros.append("Porta do OBS inválida")

    return erros


def _validar_binding(nome, cfg):
    """Um gesto isolado. Devolve `(erros, avisos, tem_acao)`."""
    erros = []
    avisos = []

    usa_cena = bool(cfg.get("use_scene", False))
    usa_som = bool(cfg.get("use_sound", False))
    usa_atalho = bool(cfg.get("use_hotkey", False))

    if not (usa_cena or usa_som or usa_atalho):
        avisos.append(f"Gesto {nome} está ativo, mas sem funcionalidade selecionada")
        return erros, avisos, False

    if usa_cena and not str(cfg.get("scene", "")).strip():
        erros.append(f"Gesto {nome}: cena está vazia")

    if usa_som:
        arquivo = str(cfg.get("sound_file", "")).strip()
        if not arquivo:
            erros.append(f"Gesto {nome}: arquivo de som está vazio")
        elif not os.path.exists(arquivo):
            # Aviso, não erro: o arquivo pode estar num drive que ainda vai ser montado,
            # e a ação de som falhando não derruba nada — só não toca.
            avisos.append(
                f"Gesto {nome}: arquivo de som não encontrado no caminho informado"
            )

    if usa_atalho and not str(cfg.get("hotkey", "")).strip():
        avisos.append(f"Gesto {nome}: atalho está vazio")

    erros += _validar_tempos(nome, cfg)
    return erros, avisos, True


def _validar_tempos(nome, cfg):
    erros = []

    try:
        hold = float(cfg.get("hold_time", 0.7))
        cooldown = float(cfg.get("cooldown", 2.0))
    except (TypeError, ValueError):
        return [f"Gesto {nome}: tempo de resposta ou cooldown não é número"]

    if hold < 0.1:
        erros.append(f"Gesto {nome}: tempo de resposta deve ser >= 0.1s")
    if cooldown < 0:
        erros.append(f"Gesto {nome}: cooldown não pode ser negativo")

    return erros


def validar(config, gestos_ativos):
    """Devolve `(erros, avisos)`, ambos listas de texto pronto para a tela.

    Com `erros` não vazio a engine não deve subir. Com só `avisos`, cabe a quem chama
    perguntar ao usuário.
    """
    erros = []
    avisos = []

    config = config or {}
    modo = config.get("modo", "automatico")

    if modo in MODOS_QUE_USAM_OBS:
        erros += _validar_obs(config.get("obs", {}) or {})

    bindings = (config.get("gestures", {}) or {}).get("bindings", {}) or {}
    ativos = set(gestos_ativos or [])

    em_uso = [(nome, cfg) for nome, cfg in bindings.items() if nome in ativos]

    if not em_uso:
        avisos.append("Nenhum gesto está ativado")
        return erros, avisos

    alguma_acao = False
    for nome, cfg in em_uso:
        erros_gesto, avisos_gesto, tem_acao = _validar_binding(nome, cfg or {})
        erros += erros_gesto
        avisos += avisos_gesto
        alguma_acao = alguma_acao or tem_acao

    if not alguma_acao:
        avisos.append("Nenhum gesto ativo possui ação efetiva")

    return erros, avisos
