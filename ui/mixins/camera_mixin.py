try:
    from PySide6.QtMultimedia import QMediaDevices
except Exception:
    QMediaDevices = None

try:
    from pygrabber.dshow_graph import FilterGraph  # type: ignore[import-not-found]
except Exception:
    FilterGraph = None

from core.capacidades_camera import (
    capacidades,
    fps_suportado,
    preset_recomendado,
    resolucao_suportada,
)
from ui.presets import RESOLUTION_PRESETS, RESOLUTION_PRESETS_REVERSED
from util.logger import get_logger

logger = get_logger(__name__)


class CameraMixin:

    @staticmethod
    def _is_virtual_camera_name(name):
        value = (name or "").strip().lower()
        virtual_tokens = (
            "obs virtual",
            "virtual camera",
            "vcam",
            "xsplit",
            "manycam",
            "snap camera",
        )
        return any(token in value for token in virtual_tokens)

    def _normalize_camera_display_name(self, name, index):
        clean_name = (name or "").strip()
        if self._is_virtual_camera_name(clean_name):
            return "OBS Virtual Camera"
        if clean_name:
            return clean_name
        return f"Câmera {index}"

    @staticmethod
    def _dshow_device_names():
        if FilterGraph is None:
            return []
        try:
            graph = FilterGraph()
            return list(graph.get_input_devices() or [])
        except Exception as exc:
            logger.debug("Falha ao listar dispositivos DirectShow: %s", exc)
            return []

    def _populate_camera_devices(self):
        """Descobre as câmeras e entrega a lista pronta para a aba. Ver `geral_contrato`.

        Antes isto manipulava o `QComboBox` diretamente — `addItem`, `setCurrentIndex`,
        `blockSignals` — e por isso só funcionava com a aba de Widgets. Agora produz dados
        e deixa a aba desenhar.
        """
        indice_desejado = int(self.estado.camera_indice)
        nome_desejado = str(self.estado.camera_dispositivo or "").strip()

        brutos = []
        if QMediaDevices is not None:
            try:
                brutos = [d.description() for d in QMediaDevices.videoInputs()]
            except Exception as exc:
                logger.debug("Falha ao listar via QMediaDevices: %s", exc)

        if not brutos:
            brutos = self._dshow_device_names()

        if brutos:
            entradas = [
                (self._normalize_camera_display_name(nome, i), i)
                for i, nome in enumerate(brutos)
            ]
        else:
            entradas = [(nome_desejado or "Câmera 0", 0)]

        # A câmera virtual vai para o fim: escolher a saída do OBS como *entrada* cria um
        # laço de vídeo, e ninguém quer isso por engano.
        entradas.sort(key=lambda item: (self._is_virtual_camera_name(item[0]), item[1]))

        escolhido = self._escolher_camera(entradas, indice_desejado, nome_desejado)
        self.geral_tab.definir_cameras(entradas, escolhido)

        nome, indice = self.geral_tab.camera_atual()
        self.estado.camera_indice = int(indice)
        self.estado.camera_dispositivo = nome

    @staticmethod
    def _preferir_fisica(entradas):
        for nome, indice in entradas:
            if not CameraMixin._is_virtual_camera_name(nome):
                return indice
        return entradas[0][1] if entradas else 0

    def _escolher_camera(self, entradas, indice_desejado, nome_desejado):
        """Índice salvo primeiro; depois o nome; por último, a primeira câmera física."""
        for _, indice in entradas:
            if int(indice) == indice_desejado:
                return indice

        if nome_desejado:
            for nome, indice in entradas:
                if nome.strip().lower() == nome_desejado.lower():
                    return indice

        return self._preferir_fisica(entradas)

    def on_camera_changed(self, indice_do_dispositivo):
        nome, _ = self.geral_tab.camera_atual()
        self.estado.camera_indice = int(indice_do_dispositivo)
        self.estado.camera_dispositivo = nome
        self.aplicar_capacidades_da_camera()

    def on_resolution_changed(self, value):
        if value not in RESOLUTION_PRESETS:
            return
        width, height = RESOLUTION_PRESETS[value]
        self.estado.camera_largura = width
        self.estado.camera_altura = height
        # O teto de FPS varia por resolução, então a lista de FPS válidos muda junto.
        self.aplicar_capacidades_da_camera()

    FPS_OFERECIDOS = (30, 60)

    def aplicar_capacidades_da_camera(self):
        """Diz à aba o que a câmera NÃO oferece. Ver D-38.

        Consulta o sistema a cada chamada (~170ms) em vez de guardar cache: capacidade em
        cache envelhece mal — trocar de webcam com dado velho esconderia modos que
        funcionam — e a consulta é barata o bastante para dispensar isso.

        Se a consulta falhar, `capacidades()` devolve vazio e **nada é desabilitado**. Um
        probe quebrado não pode trancar o usuário fora de opções que a câmera tem.
        """
        modos = capacidades(self.estado.camera_indice)
        largura = int(self.estado.camera_largura)
        altura = int(self.estado.camera_altura)

        resolucoes_off = [
            rotulo
            for rotulo, (w, h) in RESOLUTION_PRESETS.items()
            if not resolucao_suportada(modos, w, h)
        ]
        fps_off = [
            fps
            for fps in self.FPS_OFERECIDOS
            if not fps_suportado(modos, largura, altura, fps)
        ]

        self.geral_tab.definir_capacidades(
            resolucoes_off,
            fps_off,
            self._texto_do_aviso(modos, largura, altura, resolucoes_off),
            self._preset_recomendado(modos) is not None,
        )

    def _texto_do_aviso(self, modos, largura, altura, resolucoes_off):
        """A faixa de limite, em uma linha. Ver D-39, D-40 e D-45.

        Vazio quando não há limite — e vazio também quando o probe falhou, porque aí não
        sabemos de nada e afirmar seria pior que calar.

        Sem o `⚠️`: neste app ele marca falha acionável, o mesmo glifo de "não foi possível
        salvar as configurações". Aqui o texto é um fato do hardware, que o usuário não tem
        como resolver (D-45).
        """
        if not modos:
            return ""

        problemas = []

        if resolucoes_off:
            problemas.append("sem " + ", ".join(sorted(resolucoes_off)))

        if resolucao_suportada(modos, largura, altura):
            teto = modos.get((largura, altura))
            sem_fps = [
                fps
                for fps in self.FPS_OFERECIDOS
                if not fps_suportado(modos, largura, altura, fps)
            ]
            if sem_fps and teto:
                lista = "/".join(str(f) for f in sorted(sem_fps))
                problemas.append(f"máx. {int(teto)} fps em {largura}x{altura}, não {lista}")

        if not problemas:
            return ""

        return "Limites desta câmera: " + " · ".join(problemas)

    def _preset_recomendado(self, modos=None):
        """`modos` já em mãos evita um segundo probe de ~170ms no mesmo ciclo."""
        if modos is None:
            modos = capacidades(self.estado.camera_indice)
        return preset_recomendado(
            modos,
            self.estado.modo,
            list(RESOLUTION_PRESETS.values()),
            sorted(self.FPS_OFERECIDOS),
        )

    def aplicar_preset_recomendado(self):
        """Aplica o melhor modo para o modo de operação atual. Ver D-39."""
        preset = self._preset_recomendado()
        if preset is None:
            self._append_log("Não foi possível recomendar uma configuração para esta câmera.")
            return

        largura, altura, fps = preset
        self.estado.camera_largura = int(largura)
        self.estado.camera_altura = int(altura)
        self.estado.camera_fps = int(fps)

        rotulo = RESOLUTION_PRESETS_REVERSED.get((largura, altura))
        if rotulo:
            self.geral_tab.set_resolution(rotulo)
        self.geral_tab.set_fps(int(fps))

        motivo = (
            "a imagem vai para o OBS, então vale a maior resolução"
            if self.estado.modo == "automatico"
            else "sem câmera virtual, acima de 720p não melhora a detecção e só custa CPU"
        )
        self._append_log(f"Configuração recomendada: {largura}x{altura} a {fps} fps — {motivo}.")

        self.aplicar_capacidades_da_camera()
        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            self._append_log("Reinicie a captura para a nova resolução valer.")

    def on_fps_changed(self, value):
        self.estado.camera_fps = int(value)
