import QtQuick
import QtQuick.Layouts
import novo

// Uma ação do gesto (cena, som, atalho) como cartão que liga e revela o próprio campo.
//
// Hoje as três ações são um Interruptor solto seguido de um campo que fica desabilitado
// mas visível — o que dá três campos mortos na tela o tempo todo. Aqui o campo só existe
// quando a ação está ligada, e o cartão diz o que ela faz quando está desligada.
Item {
    id: raiz

    property string titulo: ""
    property string glifo: ""
    property string explicacao: ""
    property bool ligado: false
    default property alias conteudo: area.data

    signal alternado(bool v)

    Layout.fillWidth: true
    implicitHeight: coluna.implicitHeight + Tema.e4 * 2

    Rectangle {
        anchors.fill: parent
        radius: Tema.raio
        color: raiz.ligado ? Tema.elevada : Tema.superficie
        border.width: 1
        border.color: raiz.ligado ? Tema.borda : Tema.bordaSutil
        Behavior on color { ColorAnimation { duration: 140 } }

        ColumnLayout {
            id: coluna
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Tema.e4
            spacing: Tema.e3

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                Text {
                    text: raiz.glifo
                    font.family: Tema.familia
                    font.pixelSize: 15
                    color: raiz.ligado ? Tema.destaqueHover : Tema.textoApagado
                    Layout.preferredWidth: 18
                    Behavior on color { ColorAnimation { duration: 140 } }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        text: raiz.titulo
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        font.weight: Font.DemiBold
                        color: raiz.ligado ? Tema.texto : Tema.textoSecundario
                    }

                    Text {
                        visible: !raiz.ligado && raiz.explicacao !== ""
                        Layout.fillWidth: true
                        text: raiz.explicacao
                        wrapMode: Text.WordWrap
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        color: Tema.textoApagado
                    }
                }

                Rectangle {
                    implicitWidth: 38
                    implicitHeight: 21
                    radius: 11
                    color: raiz.ligado ? Tema.destaque : Tema.controle
                    border.width: 1
                    border.color: raiz.ligado ? Tema.destaque : Tema.borda
                    Behavior on color { ColorAnimation { duration: 140 } }

                    Rectangle {
                        width: 15
                        height: 15
                        radius: 8
                        y: 3
                        x: raiz.ligado ? parent.width - width - 3 : 3
                        color: raiz.ligado ? "#ffffff" : Tema.textoApagado
                        Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
                    }

                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -4
                        cursorShape: Qt.PointingHandCursor
                        onClicked: raiz.alternado(!raiz.ligado)
                    }
                }
            }

            ColumnLayout {
                id: area
                Layout.fillWidth: true
                spacing: Tema.e2
                visible: raiz.ligado
            }
        }
    }
}
