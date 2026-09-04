"""Leitura das capacidades da câmera e o fail-open que a protege. Ver D-38."""

import sys

import pytest

from core import capacidades_camera as cap


def formato(largura, altura, min_fr, max_fr, codec="MJPG"):
    """Imita uma entrada do `get_formats()` do pygrabber."""
    return {
        "media_type_str": codec,
        "width": largura,
        "height": altura,
        "min_framerate": min_fr,
        "max_framerate": max_fr,
    }


class TestCamposInvertidosDoPygrabber:
    """A armadilha que faria o filtro funcionar ao contrário.

    O pygrabber reporta `min_framerate=30, max_framerate=5` para um modo cujo range real é
    5–30 — provavelmente porque o DirectShow expõe *intervalos entre frames*, e o menor
    intervalo é o maior FPS. Ler o campo pelo nome inverteria toda a lógica.
    """

    def test_pega_o_maior_dos_dois_campos(self):
        assert cap._fps_maximo(formato(1920, 1080, 30, 5)) == 30

    def test_funciona_se_um_dia_vierem_na_ordem_certa(self):
        assert cap._fps_maximo(formato(1920, 1080, 5, 30)) == 30

    def test_campo_ausente_nao_estoura(self):
        assert cap._fps_maximo({"media_type_str": "MJPG"}) == 0


class TestFailOpen:
    """Sem dados, tudo é permitido. Um probe quebrado não pode trancar o usuário fora."""

    def test_sem_modos_toda_resolucao_passa(self):
        assert cap.resolucao_suportada({}, 1920, 1080) is True

    def test_sem_modos_todo_fps_passa(self):
        assert cap.fps_suportado({}, 1920, 1080, 240) is True

    def test_resolucao_desconhecida_nao_bloqueia_o_fps(self):
        """Quem barra uma resolução inexistente é o teste de resolução, não o de FPS."""
        modos = {(1280, 720): 30}
        assert cap.fps_suportado(modos, 1920, 1080, 60) is True

    def test_fps_maximo_sem_dados_e_none(self):
        assert cap.fps_maximo_do_dispositivo({}) is None

    def test_dispositivo_inexistente_devolve_vazio(self):
        """Não levanta: quem chama não deve precisar de try/except para montar a UI."""
        assert cap.capacidades(9999) == {}


class TestFiltragem:
    MODOS = {(640, 480): 30, (1280, 720): 60, (1920, 1080): 30}

    def test_resolucao_presente_e_suportada(self):
        assert cap.resolucao_suportada(self.MODOS, 1280, 720) is True

    def test_resolucao_ausente_e_recusada(self):
        assert cap.resolucao_suportada(self.MODOS, 3840, 2160) is False

    def test_fps_dentro_do_teto_passa(self):
        assert cap.fps_suportado(self.MODOS, 1280, 720, 60) is True

    def test_fps_acima_do_teto_e_recusado(self):
        """O caso da C920: 60 fps em 1080p não existe."""
        assert cap.fps_suportado(self.MODOS, 1920, 1080, 60) is False

    def test_o_teto_varia_por_resolucao(self):
        """Mesma câmera, mesmo FPS, vereditos diferentes — daí refiltrar ao trocar."""
        assert cap.fps_suportado(self.MODOS, 1280, 720, 60) is True
        assert cap.fps_suportado(self.MODOS, 1920, 1080, 60) is False

    def test_fps_maximo_e_o_maior_entre_as_resolucoes(self):
        assert cap.fps_maximo_do_dispositivo(self.MODOS) == 60


class TestSelecaoDeFormatos:
    def test_ignora_codecs_que_o_app_nao_usa(self, monkeypatch):
        """`core/camera.py` pede MJPEG. Um modo YUY2 a 60fps não ajuda em nada."""
        formatos = [
            formato(1920, 1080, 60, 5, codec="YUY2"),
            formato(1920, 1080, 30, 5, codec="MJPG"),
        ]
        _instalar_pygrabber_falso(monkeypatch, formatos)

        assert cap.capacidades(0) == {(1920, 1080): 30}

    def test_mantem_o_maior_fps_quando_a_resolucao_repete(self, monkeypatch):
        formatos = [formato(1280, 720, 15, 5), formato(1280, 720, 30, 5)]
        _instalar_pygrabber_falso(monkeypatch, formatos)

        assert cap.capacidades(0) == {(1280, 720): 30}

    def test_sem_modos_mjpeg_devolve_vazio(self, monkeypatch):
        """Fail-open: câmera só com YUY2 não deve ter a UI toda desabilitada."""
        _instalar_pygrabber_falso(monkeypatch, [formato(640, 480, 30, 5, codec="YUY2")])

        assert cap.capacidades(0) == {}

    def test_formato_sem_dimensao_e_ignorado(self, monkeypatch):
        formatos = [
            {"media_type_str": "MJPG", "width": 0, "height": 0},
            formato(640, 480, 30, 5),
        ]
        _instalar_pygrabber_falso(monkeypatch, formatos)

        assert cap.capacidades(0) == {(640, 480): 30}


def _instalar_pygrabber_falso(monkeypatch, formatos):
    """Substitui o FilterGraph por um que devolve os formatos dados."""

    class DispositivoFalso:
        def get_formats(self):
            return formatos

    class GrafoFalso:
        def add_video_input_device(self, indice):
            pass

        def get_input_device(self):
            return DispositivoFalso()

    modulo = type(sys)("pygrabber.dshow_graph")
    modulo.FilterGraph = GrafoFalso
    monkeypatch.setitem(sys.modules, "pygrabber.dshow_graph", modulo)
