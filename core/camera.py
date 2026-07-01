import threading

import av
import cv2
import pyvirtualcam

from util.logger import get_logger

logger = get_logger(__name__)


class CameraManager:
    def __init__(
        self,
        camera_index=0,
        camera_name="",
        width=1920,
        height=1080,
        fps=30,
        enable_virtual_camera=True,
        virtual_camera_device=None,
    ):
        self.camera_index = camera_index
        self.camera_name = camera_name
        self.width = width
        self.height = height
        self.fps = fps
        self.enable_virtual_camera = enable_virtual_camera
        self.virtual_camera_device = virtual_camera_device

        self.capture = None  # não usado — mantido para compatibilidade com código externo
        self.virtual_camera = None
        self._pyav_container = None

        self._frame_lock = threading.Condition(threading.Lock())
        self._ultimo_frame = None
        self._frame_seq = 0
        self._captura_ativa = False
        self._captura_thread = None

    def iniciar(self):
        options = {
            'video_size': f'{self.width}x{self.height}',
            'framerate': str(self.fps),
            'vcodec': 'mjpeg',
        }
        self._pyav_container = av.open(
            f'video={self.camera_name}',
            format='dshow',
            options=options,
        )

        self._ultimo_frame = None
        self._frame_seq = 0
        self._captura_ativa = True
        self._captura_thread = threading.Thread(
            target=self._loop_captura,
            daemon=True,
            name="camera-capture",
        )
        self._captura_thread.start()

        if self.enable_virtual_camera:
            try:
                self.virtual_camera = pyvirtualcam.Camera(
                    width=self.width,
                    height=self.height,
                    fps=self.fps,
                    device=self.virtual_camera_device,
                )
                logger.info("Câmera virtual ativa: %s", self.virtual_camera.device)
            except Exception as exc:
                logger.warning(
                    "Câmera virtual indisponível: %s — "
                    "No OBS: Ferramentas → Câmera Virtual → Iniciar",
                    exc,
                )
                self.virtual_camera = None
                self.enable_virtual_camera = False

    @property
    def aberta(self) -> bool:
        return self._captura_ativa and self._pyav_container is not None

    def _loop_captura(self):
        """Drena câmera via PyAV/FFmpeg DirectShow e notifica waiters a cada novo frame."""
        try:
            video = next(s for s in self._pyav_container.streams if s.type == 'video')
            for packet in self._pyav_container.demux(video):
                if not self._captura_ativa:
                    break
                try:
                    for frame in packet.decode():
                        if not self._captura_ativa:
                            break
                        arr = frame.to_ndarray(format='bgr24')
                        arr = cv2.flip(arr, 1)
                        with self._frame_lock:
                            self._ultimo_frame = arr
                            self._frame_seq += 1
                            self._frame_lock.notify_all()
                except av.AVError as exc:
                    logger.warning("Erro ao decodificar frame: %s", exc)
                    break
        except Exception as exc:
            logger.exception("Erro no loop de captura: %s", exc)
        finally:
            with self._frame_lock:
                self._captura_ativa = False
                self._frame_lock.notify_all()

    def ler_frame(self):
        """Aguarda o próximo frame NOVO e retorna sua cópia.

        Bloqueia até a thread de captura entregar um frame com seq maior que o
        último retornado — elimina frame staleness. Se a câmera for mais rápida
        que a engine, frames intermediários são descartados; retorna sempre o
        mais recente disponível ao despertar.
        """
        with self._frame_lock:
            seq_antes = self._frame_seq
            novo = self._frame_lock.wait_for(
                lambda: self._frame_seq != seq_antes or not self._captura_ativa,
                timeout=0.1,
            )
            if not novo or self._ultimo_frame is None:
                return False, None
            return True, self._ultimo_frame.copy()

    def enviar_para_virtual(self, frame_bgr):
        if not self.virtual_camera:
            return

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self.virtual_camera.send(frame_rgb)
        self.virtual_camera.sleep_until_next_frame()

    def encerrar(self):
        self._captura_ativa = False

        with self._frame_lock:
            self._frame_lock.notify_all()

        # Fecha container primeiro para desbloquear demux() bloqueado na thread
        try:
            if self._pyav_container:
                self._pyav_container.close()
        except Exception as exc:
            logger.exception("Erro ao fechar container PyAV: %s", exc)

        if self._captura_thread and self._captura_thread.is_alive():
            self._captura_thread.join(timeout=2)

        try:
            if self.virtual_camera:
                self.virtual_camera.close()
        except Exception as exc:
            logger.exception("Erro ao fechar câmera virtual: %s", exc)
