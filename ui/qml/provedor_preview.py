"""O frame da câmera indo para o QML, sem sair do processo.

A engine emite `frame_ready` com um array do OpenCV, como sempre. A janela converte para
`QImage` — que é o que ela já fazia para o `QLabel` — e guarda aqui. O QML pede
`image://preview/<n>` e recebe a mesma imagem, sem cópia atravessando fronteira nenhuma.

**Por que um provedor e não uma propriedade.** `QImage` não é um tipo que o QML saiba
desenhar vindo de uma `@Property`; `Image.source` quer uma URL. O provedor é o caminho que
o Qt oferece para ligar os dois, e é o mesmo custo do `setPixmap` de hoje.

O `<n>` na URL é obrigatório: o Qt guarda imagem em cache por URL, e sem ele o preview
congelaria no primeiro quadro. Ver `PonteShell.novo_frame`.
"""

from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class ProvedorDePreview(QQuickImageProvider):

    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._imagem = QImage()

    def definir(self, imagem):
        # `copy()` porque o buffer do OpenCV é reaproveitado no próximo quadro: sem isto o
        # QML poderia desenhar por cima de memória que a engine já está reescrevendo.
        self._imagem = imagem.copy() if imagem is not None else QImage()

    def requestImage(self, id, size, requestedSize):
        imagem = self._imagem
        if imagem.isNull():
            return QImage()

        if requestedSize.isValid() and requestedSize.width() > 0 and requestedSize.height() > 0:
            from PySide6.QtCore import Qt
            imagem = imagem.scaled(
                requestedSize, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        return imagem
