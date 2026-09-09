import QtQuick
import QtQuick.Layouts
import novo

// Item do rail lateral. Substitui a QTabBar.
//
// Aba horizontal estoura em ~6 itens; o rail vertical vai a 10 sem apertar, e é isso que
// abre espaço para as features novas sem redesenhar a navegação de novo.
Item {
    id: raiz

    property string glifo: ""
    property string rotulo: ""
    property bool selecionado: false
    property string emblema: ""

    signal ativado()

    Layout.fillWidth: true
    implicitHeight: 44

    Rectangle {
        anchors.fill: parent
        radius: Tema.raio
        color: raiz.selecionado ? Tema.destaqueFraco
             : (area.containsMouse ? Tema.controle : "transparent")
        Behavior on color { ColorAnimation { duration: 120 } }

        // A barra de seleção à esquerda: diz "você está aqui" sem depender só da cor de
        // fundo, que é o que falha para quem não distingue bem matiz.
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: 1
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: raiz.selecionado ? 22 : 0
            radius: 2
            color: Tema.destaque
            Behavior on height { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Tema.e4
            anchors.rightMargin: Tema.e3
            spacing: Tema.e3

            Text {
                text: raiz.glifo
                font.family: Tema.familia
                font.pixelSize: 16
                color: raiz.selecionado ? Tema.destaqueHover
                     : (area.containsMouse ? Tema.texto : Tema.textoApagado)
                Layout.preferredWidth: 18
                horizontalAlignment: Text.AlignHCenter
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            Text {
                Layout.fillWidth: true
                text: raiz.rotulo
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpoG
                font.weight: raiz.selecionado ? Font.DemiBold : Font.Normal
                color: raiz.selecionado ? Tema.texto
                     : (area.containsMouse ? Tema.texto : Tema.textoApagado)
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            Rectangle {
                visible: raiz.emblema !== ""
                implicitWidth: txtEmblema.implicitWidth + 12
                implicitHeight: 20
                radius: 10
                color: Tema.controle
                border.width: 1
                border.color: Tema.bordaSutil

                Text {
                    id: txtEmblema
                    anchors.centerIn: parent
                    text: raiz.emblema
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMicro
                    font.weight: Font.Bold
                    color: Tema.textoApagado
                }
            }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.ativado()
    }
}
