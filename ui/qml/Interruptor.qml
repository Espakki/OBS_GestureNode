import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Caixa de seleção do tema.
//
// O indicador do `QCheckBox` estilizado por QSS aceitava cor e borda, mas o "check" em si
// vinha do tema nativo — e com `image: none` (que era o caso) simplesmente não aparecia
// marca nenhuma: o estado ligado se distinguia só pelo preenchimento roxo. Aqui a marca é
// desenhada, então marcado parece marcado.
CheckBox {
    id: raiz

    font.pixelSize: Tema.fonte

    indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: 20
        x: raiz.leftPadding
        y: parent.height / 2 - height / 2
        radius: 5
        color: raiz.checked ? Tema.destaque : Tema.controle
        border.width: 1
        border.color: raiz.checked ? Tema.destaque
             : (raiz.hovered ? Tema.destaque : Tema.borda)

        Behavior on color { ColorAnimation { duration: 120 } }

        Canvas {
            anchors.fill: parent
            visible: raiz.checked
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = Tema.textoSobreDestaque
                ctx.lineWidth = 2.4
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(5, 10)
                ctx.lineTo(8.5, 14)
                ctx.lineTo(15, 6)
                ctx.stroke()
            }
        }
    }

    contentItem: Text {
        text: raiz.text
        font: raiz.font
        color: raiz.enabled ? Tema.texto : Tema.textoDesabilitado
        verticalAlignment: Text.AlignVCenter
        leftPadding: raiz.indicator.width + 10
    }
}
