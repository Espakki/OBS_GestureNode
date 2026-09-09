import QtQuick
import QtQuick.Layouts
import novo

// O modo de operação como cartão com descrição, não como botão de opção com tooltip.
//
// É a decisão mais consequente que o usuário toma no app — define se o software vai
// executar ações de verdade ou só observar. Hoje ela é um dos três toggles idênticos numa
// linha, e a explicação mora num tooltip que só aparece se o mouse parar em cima.
Item {
    id: raiz

    property string titulo: ""
    property string descricao: ""
    property string glifo: ""
    property bool selecionado: false

    signal escolhido()

    Layout.fillWidth: true
    implicitHeight: 92

    Rectangle {
        anchors.fill: parent
        radius: Tema.raio
        color: raiz.selecionado ? Tema.destaqueFraco
             : (area.containsMouse ? Tema.controleHover : Tema.elevada)
        border.width: raiz.selecionado ? 2 : 1
        border.color: raiz.selecionado ? Tema.destaque
             : (area.containsMouse ? Tema.bordaHover : Tema.bordaSutil)

        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }

        RowLayout {
            anchors.fill: parent
            anchors.margins: Tema.e4
            spacing: Tema.e4

            Rectangle {
                Layout.alignment: Qt.AlignTop
                width: 38
                height: 38
                radius: Tema.raioPequeno
                color: raiz.selecionado ? Tema.destaque : Tema.controle
                border.width: 1
                border.color: raiz.selecionado ? Tema.destaque : Tema.borda
                Behavior on color { ColorAnimation { duration: 120 } }

                Text {
                    anchors.centerIn: parent
                    text: raiz.glifo
                    font.family: Tema.familia
                    font.pixelSize: 17
                    color: raiz.selecionado ? Tema.textoSobreDestaque : Tema.textoApagado
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Tema.e1

                Text {
                    text: raiz.titulo
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteCorpoG
                    font.weight: Font.DemiBold
                    color: raiz.selecionado ? Tema.texto : Tema.textoSecundario
                }

                Text {
                    Layout.fillWidth: true
                    text: raiz.descricao
                    wrapMode: Text.WordWrap
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoApagado
                    lineHeight: 1.25
                }
            }

            // marca de selecionado, além da cor
            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                width: 20
                height: 20
                radius: 10
                color: raiz.selecionado ? Tema.destaque : "transparent"
                border.width: raiz.selecionado ? 0 : 1
                border.color: Tema.borda

                Canvas {
                    anchors.fill: parent
                    visible: raiz.selecionado
                    onPaint: {
                        const ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "#ffffff"
                        ctx.lineWidth = 2.2
                        ctx.lineCap = "round"
                        ctx.lineJoin = "round"
                        ctx.beginPath()
                        ctx.moveTo(5.5, 10)
                        ctx.lineTo(8.5, 13.5)
                        ctx.lineTo(14.5, 6.5)
                        ctx.stroke()
                    }
                }
            }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.escolhido()
    }
}
