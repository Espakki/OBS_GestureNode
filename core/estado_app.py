"""O estado do aplicativo, com aviso de mudança. Ver D-47.

**O problema que isto resolve.** Antes, `self.config` era um dicionário cru mutado de toda
parte, e nada avisava que ele tinha mudado. As duas consequências apareciam contadas no
código: **14 chamadas manuais** de `salvar_config_automatico()`, uma em cada lugar que
alguém lembrou de escrever, e **43 guardas** do tipo `blockSignals` / `_updating_gesture_form`,
porque carregar a config na tela disparava os mesmos handlers que um clique do usuário.

Aqui a mudança é observável. Quem quiser salvar assina uma vez, no boot, e o save deixa de
depender de alguém lembrar. A guarda de "isto é carga, não clique" sai do estado e vai
para o vínculo com o widget (`ui/vinculo.py`), onde ela existe **uma vez**.

**Sem Qt de propósito.** Este módulo não importa PySide6. Ele é o candidato natural a
sobreviver a uma troca de framework de interface, e é a razão de ele poder ser testado sem
abrir janela nenhuma.

**O dicionário continua sendo o formato de disco.** `config_bruta()` devolve o mesmo
`config.json` de sempre — nada de migração de arquivo, nada que o usuário perceba.
"""

from core import config_schema
from util.logger import get_logger

logger = get_logger(__name__)

_AUSENTE = object()


class _Campo:
    """Propriedade ligada a um caminho do config, que notifica quando muda.

    Existe para que os ~20 campos não virem 40 métodos escritos à mão. O ganho não é
    tamanho: é que a leitura e a escrita de um campo ficam **impossíveis de divergir**,
    porque são o mesmo caminho declarado uma vez.
    """

    def __init__(self, caminho, conversor=None):
        self.caminho = caminho.split(".")
        self.conversor = conversor
        self.nome = caminho

    def __set_name__(self, dono, nome):
        self.nome = nome

    def _mergulhar(self, config, criar=False):
        no = config
        for parte in self.caminho[:-1]:
            if criar:
                no = no.setdefault(parte, {})
            else:
                no = no.get(parte, {})
                if not isinstance(no, dict):
                    return {}
        return no

    def __get__(self, obj, dono=None):
        if obj is None:
            return self
        return self._mergulhar(obj._config).get(self.caminho[-1])

    def __set__(self, obj, valor):
        if self.conversor is not None:
            valor = self.conversor(valor)

        no = self._mergulhar(obj._config, criar=True)
        anterior = no.get(self.caminho[-1], _AUSENTE)

        # Só notifica se mudou de verdade. Sem isto, refletir o estado na tela devolveria
        # o mesmo valor ao estado, que notificaria, que salvaria — o laço que as 43
        # guardas existiam para cortar.
        if anterior is not _AUSENTE and anterior == valor:
            return

        no[self.caminho[-1]] = valor
        obj._notificar(self.nome, valor)


class EstadoApp:
    """Fonte única da configuração viva. Notifica quem assinar."""

    modo = _Campo("modo", str)
    max_maos = _Campo("max_maos", int)
    onboarding_feito = _Campo("onboarding_done", bool)

    camera_indice = _Campo("camera.index", int)
    camera_dispositivo = _Campo("camera.device_name", str)
    camera_largura = _Campo("camera.width", int)
    camera_altura = _Campo("camera.height", int)
    camera_fps = _Campo("camera.fps", int)
    camera_fps_processamento = _Campo("camera.process_fps", int)
    camera_virtual_ativa = _Campo("camera.enable_virtual_camera", bool)
    mostrar_esqueleto = _Campo("camera.show_skeleton", bool)
    esqueleto_na_vcam = _Campo("camera.skeleton_na_vcam", bool)

    obs_host = _Campo("obs.host", str)
    obs_porta = _Campo("obs.port", int)
    obs_senha = _Campo("obs.password", str)

    hold_padrao = _Campo("gestures.default_hold_time", float)
    cooldown_padrao = _Campo("gestures.default_cooldown", float)

    def __init__(self, config, gestos_validos):
        self._gestos_validos = list(gestos_validos)
        self._config = config_schema.normalizar(config or {}, self._gestos_validos)
        self._ouvintes = []

    # ------------------------------------------------------------------ observação

    def escutar(self, callback):
        """Registra `callback(campo, valor)`. Devolve uma função que cancela."""
        self._ouvintes.append(callback)

        def cancelar():
            if callback in self._ouvintes:
                self._ouvintes.remove(callback)

        return cancelar

    def _notificar(self, campo, valor):
        for callback in list(self._ouvintes):
            try:
                callback(campo, valor)
            except Exception:
                # Um ouvinte quebrado não pode impedir os outros de saberem da mudança —
                # nem derrubar quem estava só mexendo num slider.
                logger.exception("Ouvinte de estado falhou no campo %s", campo)

    # ------------------------------------------------------------------ gestos

    @property
    def gestos_validos(self):
        return list(self._gestos_validos)

    @property
    def gestos_ativos(self):
        return list(self._config["gestures"]["active_gestures"])

    @gestos_ativos.setter
    def gestos_ativos(self, gestos):
        validos = [g for g in gestos if g in self._gestos_validos]
        if not validos:
            raise ValueError("é preciso ao menos um gesto ativo")

        if validos == self.gestos_ativos:
            return

        self._config["gestures"]["active_gestures"] = validos
        for gesto, cfg in self._config["gestures"]["bindings"].items():
            cfg["enabled"] = gesto in validos

        self._notificar("gestos_ativos", validos)

    def binding(self, gesto):
        """Cópia do binding. **Cópia** para que ninguém escreva sem passar por aqui."""
        bindings = self._config["gestures"]["bindings"]
        if gesto not in bindings:
            bindings[gesto] = config_schema.binding_vazio(
                self.hold_padrao, self.cooldown_padrao
            )
        return dict(bindings[gesto])

    def definir_binding(self, gesto, **campos):
        """Atualiza campos de um gesto. Notifica uma vez só, se algo mudou de fato."""
        if gesto not in self._gestos_validos:
            raise KeyError(f"gesto desconhecido: {gesto}")

        bindings = self._config["gestures"]["bindings"]
        atual = bindings.setdefault(
            gesto, config_schema.binding_vazio(self.hold_padrao, self.cooldown_padrao)
        )

        mudou = False
        for chave, valor in campos.items():
            if atual.get(chave, _AUSENTE) != valor:
                atual[chave] = valor
                mudou = True

        if not mudou:
            return

        # `scene_map` é derivado dos bindings; mantê-lo à mão era garantia de divergir.
        config_schema.sincronizar_mapa_de_cenas(self._config["gestures"])
        self._notificar("binding", gesto)

    # ------------------------------------------------------------------ serialização

    def config_bruta(self):
        """O dicionário que vai para o disco e para a engine.

        Não é cópia: a engine precisa enxergar o mesmo objeto para que `aplicar_config`
        veja o valor mais recente. Quem escreve deve usar as propriedades acima.
        """
        return self._config
