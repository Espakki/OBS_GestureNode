import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// O dropdown, desenhado inteiro.
//
// **Esta é a queixa número um, e a causa dela.** No QSS o `QComboBox` era estilizado assim:
//
//     QComboBox::drop-down { border: none; width: 24px; }
//
// Sem regra para `::down-arrow`, a seta continuava vinda do tema nativo do Windows — daí a
// seta de outro século dentro de uma caixa escura. E o `QAbstractItemView` do popup tinha
// cor, mas nenhuma regra `::item`, então altura e respiro de cada linha vinham do padrão
// nativo e não combinavam com a caixa.
//
// O modo de falhar do QSS é esse: você sobrescreve um controle nativo em pedaços, e todo
// pedaço esquecido fica com a aparência da plataforma. Aqui não existe "pedaço esquecido" —
// se não desenharmos, não aparece.
ComboBox {
    id: raiz

    Layout.fillWidth: true
    Layout.preferredHeight: Tema.alturaControle

    font.pixelSize: Tema.fonte

    background: Rectangle {
        radius: Tema.raioPequeno
        color: raiz.enabled ? Tema.controle : Tema.controleDesabilitado
        border.width: 1
        border.color: raiz.activeFocus ? Tema.destaque
                                       : (raiz.hovered ? Tema.bordaHover : Tema.borda)
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }

    contentItem: Text {
        leftPadding: 12
        rightPadding: raiz.indicator.width + 8
        text: raiz.displayText
        font: raiz.font
        color: raiz.enabled ? Tema.texto : Tema.textoDesabilitado
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    // A seta. Um chevron desenhado com dois traços, que gira ao abrir — em vez do
    // triângulo do sistema que não combinava com nada.
    indicator: Item {
        x: raiz.width - width - 10
        y: raiz.topPadding + (raiz.availableHeight - height) / 2
        width: 14
        height: 14

        rotation: raiz.popup.visible ? 180 : 0
        Behavior on rotation { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }

        Canvas {
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = raiz.enabled ? Tema.textoSecundario : Tema.textoDesabilitado
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(2, 5)
                ctx.lineTo(width / 2, 10)
                ctx.lineTo(width - 2, 5)
                ctx.stroke()
            }
        }
    }

    delegate: ItemDelegate {
        width: raiz.width
        height: 36  // respiro explícito: era isto que faltava e deixava a lista espremida

        contentItem: Text {
            text: modelData
            font: raiz.font
            color: highlighted ? Tema.textoSobreDestaque : Tema.texto
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            leftPadding: 12
        }

        highlighted: raiz.highlightedIndex === index

        background: Rectangle {
            color: highlighted ? Tema.destaque : "transparent"
        }
    }

    popup: Popup {
        y: raiz.height + 4
        width: raiz.width
        // Cresce com o conteúdo até um teto, e aí rola. Sem isto uma lista com muitas
        // câmeras estouraria a janela.
        implicitHeight: Math.min(contentItem.implicitHeight + 2, 280)
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: raiz.popup.visible ? raiz.delegateModel : null
            currentIndex: raiz.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }

        background: Rectangle {
            radius: Tema.raioPequeno
            color: Tema.controle
            border.width: 1
            border.color: Tema.borda
        }

        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: 110 }
        }
    }
}
