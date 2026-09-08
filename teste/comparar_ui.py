"""Compara a aba Geral em Qt Widgets e em QML, lado a lado, no mesmo estado.

Script manual, descartável — existe só para a decisão de framework. Rode e redimensione a
janela; é no estreitamento que a diferença aparece mais.

    .venv\\Scripts\\python.exe teste\\comparar_ui.py

As duas metades leem e escrevem o **mesmo** `EstadoApp`. Mexer num toggle da esquerda muda
o da direita na hora, sem uma linha de código ligando os dois: a versão QML se liga ao
estado, e o estado avisa. É a diferença estrutural, não só a visual.
"""

import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from PySide6.QtQuickControls2 import QQuickStyle

# Antes de qualquer coisa do QtQuick: o estilo "Basic" e o unico que deixa sobrescrever
# background e contentItem dos controles. Nos estilos nativos o Qt ignora essas
# customizacoes -- e ai voltariamos ao problema do QSS, com pedacos vindo da plataforma.
QQuickStyle.setStyle("Basic")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.estado_app import EstadoApp
from ui.styles import APP_STYLESHEET
from ui.tabs.geral_tab import GeralTab
from ui.tabs.geral_tab_qml import GeralTabQml

GESTOS = ["V", "Joinha", "Mão aberta", "Punho", "Rock", "OK"]


def coluna(titulo, subtitulo, widget):
    caixa = QWidget()
    layout = QVBoxLayout(caixa)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(4)

    rotulo = QLabel(titulo)
    rotulo.setObjectName("title")
    layout.addWidget(rotulo)

    nota = QLabel(subtitulo)
    nota.setObjectName("muted")
    nota.setWordWrap(True)
    layout.addWidget(nota)

    layout.addWidget(widget, 1)
    return caixa


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    estado = EstadoApp({}, GESTOS)

    esquerda = GeralTab()
    esquerda.set_mode(estado.modo)
    esquerda.set_max_maos(estado.max_maos)
    esquerda.set_resolution("720p")
    esquerda.set_fps(estado.camera_fps)
    esquerda.set_esqueleto(estado.mostrar_esqueleto, estado.esqueleto_na_vcam)
    esquerda.camera_device_combo.addItems(
        ["HD Pro Webcam C920", "Integrated Camera", "OBS Virtual Camera"]
    )
    esquerda.camera_aviso.setText(
        "Limites desta câmera: sem 1080p · máx. 30 fps em 1280x720, não 60"
    )
    esquerda.camera_aviso.setVisible(True)
    esquerda.usar_recomendado_button.setVisible(True)
    esquerda.health_camera.setText("● Câmera: Pronta (HD Pro Webcam C920)")
    esquerda.health_camera.setStyleSheet("color: #94a3b8; font-weight: 600;")
    esquerda.health_obs.setText("● OBS: Não testado")
    esquerda.health_obs.setStyleSheet("color: #94a3b8; font-weight: 600;")
    esquerda.health_gestos.setText("● Gestos: 6 gesto(s) ativos")
    esquerda.health_gestos.setStyleSheet("color: #22c55e; font-weight: 600;")

    direita = GeralTabQml(estado)
    direita.ponte.definir_cameras(
        ["HD Pro Webcam C920", "Integrated Camera", "OBS Virtual Camera"], 0
    )
    direita.ponte.definir_capacidades(
        resolucoes_off=["1080p"],
        fps_off=[60],
        aviso="Limites desta câmera: sem 1080p · máx. 30 fps em 1280x720, não 60",
        tem_recomendacao=True,
    )
    direita.ponte.definir_saude(
        [
            ("Câmera", "idle", "Pronta (HD Pro Webcam C920)"),
            ("OBS", "idle", "Não testado"),
            ("Gestos", "ok", "6 gesto(s) ativos"),
        ]
    )

    # Os pedidos da versao QML caem no mesmo estado, para os dois lados andarem juntos.
    direita.ponte.modoPedido.connect(lambda modo: setattr(estado, "modo", modo))
    direita.ponte.maosPedidas.connect(lambda n: setattr(estado, "max_maos", n))
    direita.ponte.fpsPedido.connect(lambda f: setattr(estado, "camera_fps", f))

    def ecoar(campo, valor):
        print(f"estado mudou: {campo} = {valor}")
        esquerda.set_mode(estado.modo)
        esquerda.set_max_maos(estado.max_maos)
        esquerda.set_fps(estado.camera_fps)
        esquerda.set_esqueleto(estado.mostrar_esqueleto, estado.esqueleto_na_vcam)

    estado.escutar(ecoar)

    janela = QWidget()
    janela.setWindowTitle("Aba Geral — Widgets (hoje) x QML (proposta)")
    janela.resize(1180, 820)
    linha = QHBoxLayout(janela)
    linha.setSpacing(0)

    linha.addWidget(
        coluna(
            "HOJE — Qt Widgets",
            "Dropdown com seta do sistema, popup sem respiro, larguras fixas.",
            esquerda,
        ),
        1,
    )
    linha.addWidget(
        coluna(
            "PROPOSTA — QML",
            "Tudo desenhado por nós. Estreite a janela: os campos empilham.",
            direita,
        ),
        1,
    )

    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
