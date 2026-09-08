import QtQuick
import QtQuick.Layouts

// Rótulo + controle, que **empilha quando a janela estreita**.
//
// É a segunda queixa: responsividade. O `QFormLayout` do Widgets mantém rótulo e controle
// lado a lado sempre; estreitando a janela, o controle é espremido até ficar inútil. Não
// existe ponto de quebra em QLayout — a ideia não faz parte do modelo.
//
// Aqui é uma linha: abaixo de `Tema.larguraDeQuebra`, vira coluna.
ColumnLayout {
    id: raiz

    property string rotulo: ""
    default property alias conteudo: area.data

    Layout.fillWidth: true
    spacing: 6

    readonly property bool estreito: raiz.width > 0 && raiz.width < Tema.larguraDeQuebra

    GridLayout {
        Layout.fillWidth: true
        columns: raiz.estreito ? 1 : 2
        columnSpacing: Tema.espacoLinha
        rowSpacing: 6

        Text {
            text: raiz.rotulo
            color: Tema.texto
            font.pixelSize: Tema.fonte
            Layout.preferredWidth: raiz.estreito ? -1 : 86
            Layout.alignment: raiz.estreito ? Qt.AlignLeft : (Qt.AlignLeft | Qt.AlignVCenter)
        }

        RowLayout {
            id: area
            Layout.fillWidth: true
            spacing: Tema.espaco
        }
    }
}
