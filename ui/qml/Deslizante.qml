import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Slider com o valor ao lado. Substitui o par `QSlider` + `QDoubleSpinBox`.
//
// Em Widgets eram dois controles independentes, e mantê-los mostrando o mesmo número
// exigia quatro handlers com `blockSignals` (o que hoje o `ui/vinculo.py` centraliza).
// Aqui o valor é um só: o número ao lado **lê** o slider, então não há o que sincronizar.
RowLayout {
    id: raiz

    property real valor: 0
    property real minimo: 0
    property real maximo: 10
    property real passo: 0.1
    property string sufixo: "s"

    signal editado(real novo)

    Layout.fillWidth: true
    spacing: Tema.espaco

    Slider {
        id: controle
        Layout.fillWidth: true
        from: raiz.minimo
        to: raiz.maximo
        stepSize: raiz.passo
        snapMode: Slider.SnapAlways
        value: raiz.valor

        // `moved` e não `valueChanged`: o segundo dispara também quando o valor vem do
        // estado, e aí refletir viraria edição — o mesmo laço do D-41, em outra roupa.
        onMoved: raiz.editado(value)

        background: Rectangle {
            x: controle.leftPadding
            y: controle.topPadding + controle.availableHeight / 2 - height / 2
            width: controle.availableWidth
            height: 8
            radius: 4
            color: Tema.borda

            Rectangle {
                width: controle.visualPosition * parent.width
                height: parent.height
                radius: 4
                color: Tema.destaque
            }
        }

        handle: Rectangle {
            x: controle.leftPadding + controle.visualPosition * (controle.availableWidth - width)
            y: controle.topPadding + controle.availableHeight / 2 - height / 2
            width: 20
            height: 20
            radius: 10
            color: controle.pressed ? Tema.destaquePressionado
                 : (controle.hovered ? Tema.destaqueHover : Tema.destaque)
            border.width: 2
            border.color: Tema.fundo

            Behavior on color { ColorAnimation { duration: 120 } }
        }
    }

    // Só leitura, e de propósito: digitar aqui exigiria validar faixa, tratar texto
    // parcial e decidir quando comitar. O slider já dá o controle fino com as setas.
    Rectangle {
        Layout.preferredWidth: 68
        Layout.preferredHeight: Tema.alturaControle
        radius: Tema.raioPequeno
        color: Tema.controle
        border.width: 1
        border.color: Tema.borda

        Text {
            anchors.centerIn: parent
            text: controle.value.toFixed(1) + raiz.sufixo
            font.pixelSize: Tema.fonte
            font.weight: Font.DemiBold
            color: Tema.texto
        }
    }
}
