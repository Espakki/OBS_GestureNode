import threading
import time

import av
import cv2
import pyvirtualcam

from util.logger import get_logger

logger = get_logger(__name__)

# FPS que toda webcam DirectShow aceita. Serve de rede quando o modo pedido não existe —
# a C920, por exemplo, não faz 60 fps em resolução nenhuma. Ver D-32.
FPS_SEGURO = 30


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

        # Mensagem para a UI quando algo foi ajustado sozinho (ex.: fallback de FPS).
        self.aviso = ""

        self.capture = None  # não usado — mantido para compatibilidade com código externo
        self.virtual_camera = None
        self._pyav_container = None

        self._frame_lock = threading.Condition(threading.Lock())
        self._ultimo_frame = None
        self._frame_seq = 0
        self._captura_ativa = False
        self._captura_thread = None

    def _iniciar_virtual_cam_com_timeout(self, timeout=3.0):
        """Inicializa pyvirtualcam em thread daemon com timeout.

        pyvirtualcam.Camera() trava indefinidamente quando o OBS segura o driver
        DirectShow exclusivamente. O timeout garante que o PyAV (preview) sempre
        inicia mesmo se a câmera virtual não estiver disponível.

        Ordem correta de uso: fechar OBS → iniciar app → abrir OBS e adicionar
        "OBS Virtual Camera" como fonte "Dispositivo de captura de vídeo".
        """
        cam_result = [None]
        cam_error = [None]

        def _criar():
            try:
                cam_result[0] = pyvirtualcam.Camera(
                    width=self.width,
                    height=self.height,
                    fps=self.fps,
                    device=self.virtual_camera_device,
                )
            except Exception as exc:
                cam_error[0] = exc

        t = threading.Thread(target=_criar, daemon=True, name="vcam-init")
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            logger.warning(
                "Câmera virtual travou na inicialização — OBS pode estar segurando o driver. "
                "Ordem correta: feche o OBS, inicie o app, depois abra o OBS e adicione "
                "'OBS Virtual Camera' como fonte."
            )
            self.enable_virtual_camera = False
            return None

        if cam_error[0] is not None:
            logger.warning("Câmera virtual indisponível: %s", cam_error[0])
            self.enable_virtual_camera = False
            return None

        logger.info("Câmera virtual ativa: %s", cam_result[0].device)
        return cam_result[0]

    def _tentar_abrir(self, fps):
        return av.open(
            f'video={self.camera_name}',
            format='dshow',
            options={
                'video_size': f'{self.width}x{self.height}',
                'framerate': str(int(fps)),
                'vcodec': 'mjpeg',
            },
        )

    def _abrir_container(self, tentativas=3, espera=0.8):
        """Abre o dispositivo DirectShow, com retry e fallback de FPS.

        **O DirectShow devolve `[Errno 5] I/O error` para dois problemas diferentes**, e
        não dá para distinguir pelo erro:

        1. Dispositivo ainda ocupado — some sozinho em ~1s. O `container.close()` anterior
           foi medido em 2.2s, e por um instante depois dele o device segue exclusivo.
        2. **Modo não suportado** — não some nunca. A C920, por exemplo, não aceita 60 fps
           em resolução nenhuma; pedir 60 falha exatamente como se estivesse ocupada.

        Insistir só resolve o caso 1. Por isso, esgotadas as tentativas, tenta uma vez com
        `FPS_SEGURO` antes de desistir: se abrir, o problema era o modo, e o usuário recebe
        um aviso dizendo isso em vez de "câmera ocupada", que mandaria ele caçar o programa
        errado.
        """
        ultimo_erro = None

        for tentativa in range(1, tentativas + 1):
            try:
                return self._tentar_abrir(self.fps)
            except Exception as exc:
                ultimo_erro = exc
                if tentativa < tentativas:
                    logger.warning(
                        "Câmera não abriu (tentativa %d/%d): %s", tentativa, tentativas, exc
                    )
                    time.sleep(espera)

        if int(self.fps) != FPS_SEGURO:
            logger.warning(
                "Câmera não aceitou %s fps; tentando %s fps", self.fps, FPS_SEGURO
            )
            try:
                container = self._tentar_abrir(FPS_SEGURO)
                self.aviso = (
                    f"A câmera não aceita {self.fps} fps nesta resolução. "
                    f"Usando {FPS_SEGURO} fps."
                )
                logger.warning(self.aviso)
                self.fps = FPS_SEGURO
                return container
            except Exception:
                pass  # o erro que importa é o original

        raise ultimo_erro

    def iniciar(self):
        """Abre câmera virtual e captura. Se falhar no meio, desfaz o que já abriu.

        Sem o rollback, um `av.open` que falha deixava a câmera virtual aberta para
        sempre: quem chama trata a exceção e desiste, e o `encerrar()` nunca roda. Cada
        tentativa frustrada vazava um produtor de VCam, e como só existe um, a tentativa
        seguinte passava a esbarrar no timeout de 3s da própria sobra.
        """
        self.aviso = ""

        try:
            # Container PRIMEIRO. Ele é o que pode falhar por formato e o que pode cair no
            # fallback de FPS — só depois dele o `self.fps` efetivo é conhecido. Criar a
            # câmera virtual antes deixaria ela travada num FPS que a captura não entrega.
            self._pyav_container = self._abrir_container()

            if self.enable_virtual_camera:
                self.virtual_camera = self._iniciar_virtual_cam_com_timeout()

            self._ultimo_frame = None
            self._frame_seq = 0
            self._captura_ativa = True
            self._captura_thread = threading.Thread(
                target=self._loop_captura,
                daemon=True,
                name="camera-capture",
            )
            self._captura_thread.start()
        except Exception:
            self.encerrar()
            raise

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
        h, w = frame_rgb.shape[:2]
        if h != self.height or w != self.width:
            frame_rgb = cv2.resize(
                frame_rgb, (self.width, self.height), interpolation=cv2.INTER_LINEAR
            )
        self.virtual_camera.send(frame_rgb)
        self.virtual_camera.sleep_until_next_frame()

    def _fechar_container(self):
        """Fecha o container PyAV. Idempotente — pode ser chamado quantas vezes for."""
        container, self._pyav_container = self._pyav_container, None
        if container is None:
            return
        try:
            container.close()
        except Exception as exc:
            logger.exception("Erro ao fechar container PyAV: %s", exc)

    def encerrar(self):
        """Libera câmera e câmera virtual. Só retorna depois que a captura parou.

        A ordem importa. A versão anterior fechava o container ANTES de esperar a thread,
        ou seja, puxava o container por baixo de um `demux()` em andamento — o que podia
        deixar o dispositivo preso e fazia o `iniciar()` seguinte falhar com
        `[Errno 5] I/O error`.

        Agora o caminho normal é: sinalizar, esperar a thread sair sozinha (ela checa a
        flag a cada pacote, ~1 frame), e só então fechar o container, sem concorrência.
        Fechar por baixo do `demux()` vira o plano B, para o caso de a thread estar
        travada esperando um pacote que nunca vem (câmera desconectada).
        """
        self._captura_ativa = False

        with self._frame_lock:
            self._frame_lock.notify_all()

        thread = self._captura_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.5)

            if thread.is_alive():
                logger.warning(
                    "Thread de captura não saiu sozinha; forçando o fechamento do container"
                )
                self._fechar_container()
                thread.join(timeout=2)

                if thread.is_alive():
                    logger.error(
                        "Thread de captura segue viva após o encerramento — "
                        "o dispositivo pode continuar ocupado"
                    )

        self._fechar_container()
        self._captura_thread = None

        try:
            if self.virtual_camera:
                self.virtual_camera.close()
        except Exception as exc:
            logger.exception("Erro ao fechar câmera virtual: %s", exc)
        finally:
            self.virtual_camera = None
