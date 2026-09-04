"""Abertura da câmera: retry de dispositivo ocupado vs fallback de modo. Ver D-32.

O DirectShow devolve o MESMO `[Errno 5] I/O error` para "dispositivo ocupado" e para
"modo não suportado". O primeiro passa sozinho, o segundo nunca — e insistir num modo que
a câmera não tem só gasta tempo e culpa o programa errado.
"""

import pytest

from core.camera import FPS_SEGURO, CameraManager


class ErroDoDirectShow(OSError):
    """Imita o [Errno 5] que o PyAV levanta nos dois casos."""


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    """Neutraliza os sleeps entre tentativas — o teste não precisa esperar de verdade."""
    monkeypatch.setattr("core.camera.time.sleep", lambda _: None)


def camera(fps=30):
    return CameraManager(
        camera_name="qualquer", width=1280, height=720, fps=fps,
        enable_virtual_camera=False,
    )


class TestDispositivoOcupado:
    def test_desiste_apos_as_tentativas_quando_o_fps_ja_e_o_seguro(self):
        """Sem fallback possível, o erro original tem de chegar a quem chamou."""
        cam = camera(fps=FPS_SEGURO)
        tentativas = []

        def sempre_falha(fps):
            tentativas.append(fps)
            raise ErroDoDirectShow("[Errno 5] I/O error")

        cam._tentar_abrir = sempre_falha

        with pytest.raises(ErroDoDirectShow):
            cam._abrir_container(tentativas=3)

        assert tentativas == [FPS_SEGURO] * 3, "não deve tentar um fallback redundante"

    def test_sucesso_numa_tentativa_seguinte_nao_gera_aviso(self):
        """Dispositivo que liberou no meio do caminho é caso normal, não merece alarme."""
        cam = camera(fps=FPS_SEGURO)
        chamadas = []

        def falha_uma_vez(fps):
            chamadas.append(fps)
            if len(chamadas) == 1:
                raise ErroDoDirectShow("ocupado")
            return "container"

        cam._tentar_abrir = falha_uma_vez

        assert cam._abrir_container(tentativas=3) == "container"
        assert cam.aviso == ""


class TestFallbackDeFps:
    def test_cai_para_o_fps_seguro_quando_o_pedido_nao_existe(self):
        """O caso da C920: 60 fps não existe em resolução nenhuma."""
        cam = camera(fps=60)
        tentativas = []

        def so_aceita_o_seguro(fps):
            tentativas.append(fps)
            if fps != FPS_SEGURO:
                raise ErroDoDirectShow("[Errno 5] I/O error")
            return "container"

        cam._tentar_abrir = so_aceita_o_seguro

        assert cam._abrir_container(tentativas=2) == "container"
        assert tentativas == [60, 60, FPS_SEGURO]

    def test_fps_efetivo_e_atualizado(self):
        """Quem lê `cam.fps` depois precisa ver o que está rodando, não o que foi pedido.

        A câmera virtual é criada DEPOIS do container justamente por isso — criá-la antes
        a deixaria presa num FPS que a captura não entrega.
        """
        cam = camera(fps=60)
        cam._tentar_abrir = lambda fps: (
            "container" if fps == FPS_SEGURO else (_ for _ in ()).throw(ErroDoDirectShow())
        )

        cam._abrir_container(tentativas=1)

        assert cam.fps == FPS_SEGURO

    def test_aviso_explica_o_que_houve(self):
        """A mensagem não pode dizer "ocupada" — mandaria o usuário caçar outro programa."""
        cam = camera(fps=60)
        cam._tentar_abrir = lambda fps: (
            "container" if fps == FPS_SEGURO else (_ for _ in ()).throw(ErroDoDirectShow())
        )

        cam._abrir_container(tentativas=1)

        assert "60" in cam.aviso and str(FPS_SEGURO) in cam.aviso
        assert "ocupada" not in cam.aviso.lower()

    def test_erro_original_vence_quando_nem_o_fallback_abre(self):
        """Câmera realmente ocupada não pode virar mensagem de FPS."""
        cam = camera(fps=60)

        def sempre_falha(fps):
            raise ErroDoDirectShow("[Errno 5] I/O error")

        cam._tentar_abrir = sempre_falha

        with pytest.raises(ErroDoDirectShow):
            cam._abrir_container(tentativas=2)

        assert cam.aviso == "", "sem fallback bem-sucedido, não há o que avisar"
