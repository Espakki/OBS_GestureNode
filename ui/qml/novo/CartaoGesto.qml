import QtQuick
import QtQuick.Layouts
import novo

// O cartão da grade de gestos, na interface nova.
//
// Carrega o interruptor de "ativo", então o diálogo modal `open_gesture_selector_dialog`
// deixa de ser necessário: ativar e configurar param de ser dois lugares.
//
// Ícone com altura fixa e rótulo com altura reservada — na grade antiga a `Image` era
// esticada pelo ColumnLayout e empurrava o nome para fora do cartão.
Item {
    id: raiz

    property string nome: ""
    property string icone: ""
    property bool ativo: true
    property bool selecionado: false
    property string resumo: ""

    signal escolhido()
    signal alternado(bool ligado)

    implicitWidth: 148
    implicitHeight: 168

    Rectangle {
        id: cartao
        anchors.fill: parent
        radius: Tema.raio
        color: raiz.selecionado ? Tema.destaqueFraco
             : (area.containsMouse ? Tema.controleHover : Tema.elevada)
        border.width: raiz.selecionado ? 2 : 1
        border.color: raiz.selecionado ? Tema.destaque
             : (area.containsMouse ? Tema.bordaHover : Tema.bordaSutil)
        clip: true

        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Tema.e3
            anchors.topMargin: Tema.e3 + 24
            spacing: Tema.e2

            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 58
                Layout.preferredHeight: 58
                source: raiz.icone
                sourceSize.width: 116
                sourceSize.height: 116
                fillMode: Image.PreserveAspectFit
                opacity: raiz.ativo ? 1.0 : 0.28
                Behavior on opacity { NumberAnimation { duration: 150 } }
            }

            Text {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                text: raiz.nome
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpo
                font.weight: Font.DemiBold
                color: raiz.ativo ? (raiz.selecionado ? Tema.texto : Tema.textoSecundario)
                                  : Tema.textoDesabilitado
            }

            Text {
                Layout.fillWidth: true
                text: raiz.ativo ? (raiz.resumo || "sem ação") : "inativo"
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                color: raiz.ativo && raiz.resumo ? Tema.textoApagado : Tema.textoDesabilitado
            }

            Item { Layout.fillHeight: true }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.escolhido()
    }

    // Depois do MouseArea do cartão, senão o clique no interruptor seria comido por ele.
    Rectangle {
        id: interruptor
        x: Tema.e3
        y: Tema.e3
        width: 34
        height: 19
        radius: 10
        color: raiz.ativo ? Tema.destaque : Tema.controle
        border.width: 1
        border.color: raiz.ativo ? Tema.destaque : Tema.borda
        Behavior on color { ColorAnimation { duration: 140 } }

        Rectangle {
            width: 13
            height: 13
            radius: 7
            y: 3
            x: raiz.ativo ? parent.width - width - 3 : 3
            color: raiz.ativo ? "#ffffff" : Tema.textoApagado
            Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        }

        MouseArea {
            anchors.fill: parent
            anchors.margins: -5
            cursorShape: Qt.PointingHandCursor
            onClicked: raiz.alternado(!raiz.ativo)
        }
    }

    Text {
        visible: raiz.selecionado
        anchors.right: parent.right
        anchors.rightMargin: Tema.e3
        anchors.top: parent.top
        anchors.topMargin: Tema.e3 + 3
        text: "EDITANDO"
        font.family: Tema.familia
        font.pixelSize: Tema.fonteMicro
        font.weight: Font.Bold
        font.letterSpacing: 0.5
        color: Tema.destaqueHover
    }
}
