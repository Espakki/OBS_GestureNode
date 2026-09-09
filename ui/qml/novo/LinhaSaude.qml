import QtQuick
import QtQuick.Layouts
import novo

// Uma linha do painel de saúde, agora no painel direito — perto de onde o olho já está
// durante a operação, e não no fim de uma coluna rolável na aba Geral.
Item {
    id: raiz

    property string titulo: ""
    property string detalhe: ""
    property color cor: Tema.neutro

    Layout.fillWidth: true
    implicitHeight: 34

    RowLayout {
        anchors.fill: parent
        spacing: Tema.e3

        Rectangle {
            width: 7
            height: 7
            radius: 4
            color: raiz.cor
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            text: raiz.titulo
            font.family: Tema.familia
            font.pixelSize: Tema.fonteMiuda
            color: Tema.textoApagado
            Layout.preferredWidth: 78
        }

        Text {
            Layout.fillWidth: true
            text: raiz.detalhe
            elide: Text.ElideRight
            font.family: Tema.familia
            font.pixelSize: Tema.fonteMiuda
            font.weight: Font.DemiBold
            color: Tema.textoSecundario
        }
    }
}
