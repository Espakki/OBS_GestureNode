import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// O botão de opção (Modo, Mãos, Resolução, FPS, Esqueleto).
//
// Equivale ao `QPushButton#optionToggle` do QSS, com uma diferença que é o ponto do
// exercício: aqui **todo** o desenho é nosso. No Qt Widgets o botão é desenhado pelo tema
// nativo e o QSS sobrescreve pedaços; o que você esquecer continua com a cara do Windows.
// É daí que vem o "cheiro de software antigo".
Button {
    id: raiz

    // `Layout.fillWidth` no lugar de `setMinimumWidth(92)`: o botão acompanha a janela em
    // vez de reservar largura fixa. São os 33 tamanhos fixos que travavam o redimensionamento.
    Layout.fillWidth: true
    Layout.preferredHeight: Tema.alturaControle
    Layout.minimumWidth: 72

    checkable: true
    font.pixelSize: Tema.fonte
    font.weight: Font.DemiBold

    // A transição existe porque ela é uma linha aqui. Em Widgets exigiria QPropertyAnimation
    // por propriedade, e por isso o app não tem nenhuma.
    background: Rectangle {
        radius: Tema.raio
        color: {
            if (!raiz.enabled)
                return Tema.controleDesabilitado
            if (raiz.checked)
                return raiz.pressed ? Tema.destaquePressionado
                                    : (raiz.hovered ? Tema.destaqueHover : Tema.destaque)
            if (raiz.pressed)
                return Tema.controlePressionado
            return raiz.hovered ? Tema.controleHover : Tema.controle
        }
        border.width: 1
        border.color: {
            if (!raiz.enabled)
                return Tema.bordaDesabilitada
            if (raiz.checked)
                return raiz.hovered ? Tema.destaqueHover : Tema.destaque
            return raiz.hovered ? Tema.bordaHover : Tema.borda
        }

        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }

    contentItem: Text {
        text: raiz.text
        font: raiz.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        color: {
            if (!raiz.enabled)
                return Tema.textoDesabilitado
            if (raiz.checked)
                return Tema.textoSobreDestaque
            return raiz.hovered ? Tema.texto : Tema.textoSecundario
        }
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    ToolTip.visible: hovered && ToolTip.text !== ""
    ToolTip.delay: 500
}
