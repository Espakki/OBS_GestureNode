import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// Slider com valor E leitura semântica.
//
// Hoje o controle mostra "1.2s" e mais nada. O número sozinho não diz se está bom: o
// usuário não tem como saber que 0,6s dispara sozinho durante a fala e que 3s parece
// travado. A faixa nomeada embaixo é o que transforma o número em decisão.
ColumnLayout {
    id: raiz

    property string rotulo: ""
    property real valor: 1.0
    property real minimo: 0.5
    property real maximo: 5.0
    property real passo: 0.1
    property string sufixo: "s"
    property var faixas: []   // [{ ate: 1.0, texto: "...", cor: Tema.atencao }, ...]

    signal editado(real novo)

    readonly property var faixaAtual: {
        for (var i = 0; i < faixas.length; i++)
            if (valor <= faixas[i].ate) return faixas[i]
        return faixas.length ? faixas[faixas.length - 1] : null
    }

    Layout.fillWidth: true
    spacing: Tema.e2

    RowLayout {
        Layout.fillWidth: true
        spacing: Tema.e3

        Text {
            text: raiz.rotulo
            font.family: Tema.familia
            font.pixelSize: Tema.fonteCorpo
            color: Tema.textoSecundario
        }

        Item { Layout.fillWidth: true }

        Text {
            text: raiz.valor.toFixed(1) + raiz.sufixo
            font.family: Tema.familia
            font.pixelSize: Tema.fonteCorpoG
            font.weight: Font.Bold
            color: Tema.texto
        }
    }

    Slider {
        id: controle
        Layout.fillWidth: true
        Layout.preferredHeight: 24
        from: raiz.minimo
        to: raiz.maximo
        stepSize: raiz.passo
        snapMode: Slider.SnapAlways
        value: raiz.valor

        // `moved` e não `valueChanged`: o segundo dispara também quando o valor vem do
        // estado, e aí refletir viraria edição — o mesmo laço do D-41 em outra roupa.
        onMoved: raiz.editado(value)

        background: Rectangle {
            x: controle.leftPadding
            y: controle.topPadding + controle.availableHeight / 2 - height / 2
            width: controle.availableWidth
            height: 6
            radius: 3
            color: Tema.controle

            Rectangle {
                width: controle.visualPosition * parent.width
                height: parent.height
                radius: 3
                color: Tema.destaque
            }
        }

        handle: Rectangle {
            x: controle.leftPadding + controle.visualPosition * (controle.availableWidth - width)
            y: controle.topPadding + controle.availableHeight / 2 - height / 2
            width: 18
            height: 18
            radius: 9
            color: controle.pressed ? Tema.destaquePressionado : Tema.destaque
            border.width: 3
            border.color: Tema.fundo
        }
    }

    RowLayout {
        Layout.fillWidth: true
        visible: raiz.faixaAtual !== null
        spacing: Tema.e2

        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: raiz.faixaAtual ? raiz.faixaAtual.cor : Tema.neutro
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            Layout.fillWidth: true
            text: raiz.faixaAtual ? raiz.faixaAtual.texto : ""
            wrapMode: Text.WordWrap
            font.family: Tema.familia
            font.pixelSize: Tema.fonteMicro
            color: Tema.textoApagado
        }
    }
}
