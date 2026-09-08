import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Área rolável cuja barra **não passa por cima do conteúdo**. Ver D-49.
//
// O `ScrollView` do Qt Quick sobrepõe a barra ao conteúdo por padrão — herança de
// interface de celular, onde a barra some sozinha. No desktop ela fica visível enquanto há
// o que rolar, e passa por cima do texto e da borda direita dos controles.
//
// A correção é reservar a faixa: o conteúdo recebe uma margem à direita do tamanho da
// barra, e a barra ocupa exatamente essa faixa. Nada se sobrepõe.
//
// A barra também é desenhada aqui. A padrão é cinza-claro e destoa do tema — e é
// exatamente o tipo de detalhe que soma para a sensação de "software de outra época".
Item {
    id: raiz

    default property alias conteudo: coluna.data
    property alias espacamento: coluna.spacing
    property int margem: Tema.espaco

    readonly property int larguraDaBarra: 10

    Flickable {
        id: rolagem
        anchors.fill: parent
        anchors.margins: raiz.margem

        contentWidth: width
        contentHeight: coluna.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ColumnLayout {
            id: coluna
            // A margem existe só quando há barra: sem conteúdo para rolar, o espaço volta
            // para o conteúdo em vez de ficar uma faixa vazia sem explicação.
            width: rolagem.width - (barra.visible ? raiz.larguraDaBarra + 4 : 0)
            spacing: Tema.espacoLinha
        }

        ScrollBar.vertical: ScrollBar {
            id: barra
            policy: ScrollBar.AsNeeded
            width: raiz.larguraDaBarra

            contentItem: Rectangle {
                implicitWidth: raiz.larguraDaBarra
                radius: width / 2
                color: barra.pressed ? Tema.destaque
                     : (barra.hovered ? Tema.bordaHover : Tema.borda)
                Behavior on color { ColorAnimation { duration: 120 } }
            }

            background: Rectangle {
                color: "transparent"
            }
        }
    }
}
