import QtQuick
import QtQuick.Layouts
import novo

// O estado do sistema como chip, na barra superior. Substitui os TRÊS lugares onde o
// estado é dito hoje (painel "Status do sistema", status_label e obs_footer_label com
// emoji) por um só, sempre visível, com a mesma gramática para todos os assuntos.
Rectangle {
    id: raiz

    property string texto: ""
    property color cor: Tema.neutro
    property color corFundo: Tema.elevada
    property bool pulsando: false

    implicitWidth: linha.implicitWidth + Tema.e3 * 2
    implicitHeight: 30
    radius: 15
    color: corFundo
    border.width: 1
    border.color: Qt.rgba(cor.r, cor.g, cor.b, 0.35)

    RowLayout {
        id: linha
        anchors.centerIn: parent
        spacing: Tema.e2

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: raiz.cor
            Layout.alignment: Qt.AlignVCenter

            SequentialAnimation on opacity {
                running: raiz.pulsando
                loops: Animation.Infinite
                NumberAnimation { to: 0.35; duration: 700; easing.type: Easing.InOutQuad }
                NumberAnimation { to: 1.0;  duration: 700; easing.type: Easing.InOutQuad }
            }
        }

        Text {
            text: raiz.texto
            color: Tema.textoSecundario
            font.family: Tema.familia
            font.pixelSize: Tema.fonteMiuda
            font.weight: Font.DemiBold
        }
    }
}
