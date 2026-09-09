import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// Campo que grava uma combinação de teclas. Mesma lógica do D-50: não traduz nada aqui,
// recolhe os números do evento e entrega ao Python, que chama `ui/atalho_capturado.py` —
// a mesma função das outras duas interfaces. Reimplementar a tradução aqui perderia a
// defesa contra AltGr, e o teste continuaria verde porque exercita outra tela.
Item {
    id: raiz

    property bool ativo: true

    Layout.fillWidth: true
    implicitHeight: Tema.alturaControle

    Rectangle {
        anchors.fill: parent
        radius: Tema.raioPequeno
        color: ponteGestos.capturando ? Tema.destaquePressionado
             : (raiz.ativo ? Tema.controle : Tema.controleDesabilitado)
        border.width: ponteGestos.capturando ? 2 : 1
        border.color: ponteGestos.capturando ? Tema.destaqueHover
             : (area.containsMouse ? Tema.bordaHover : Tema.borda)

        Behavior on color { ColorAnimation { duration: 140 } }
        Behavior on border.color { ColorAnimation { duration: 140 } }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Tema.e3
            anchors.rightMargin: Tema.e3
            spacing: Tema.e2

            // Teclas como pastilhas, quando há atalho gravado e não está capturando.
            Repeater {
                model: (!ponteGestos.capturando && ponteGestos.atalho)
                    ? ponteGestos.atalho.split("+") : []

                delegate: Rectangle {
                    required property string modelData
                    implicitWidth: tecla.implicitWidth + 16
                    implicitHeight: 24
                    radius: 5
                    color: Tema.elevada
                    border.width: 1
                    border.color: Tema.borda

                    Text {
                        id: tecla
                        anchors.centerIn: parent
                        text: modelData
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        color: Tema.textoSecundario
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: ponteGestos.capturando || !ponteGestos.atalho
                elide: Text.ElideRight
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpo
                text: {
                    if (ponteGestos.capturando)
                        return ponteGestos.atalhoParcial || "Pressione as teclas..."
                    return "Clique para capturar (ESC cancela)"
                }
                color: {
                    if (!raiz.ativo) return Tema.textoDesabilitado
                    if (ponteGestos.capturando) return Tema.textoSobreDestaque
                    return Tema.textoApagado
                }
            }

            Item {
                Layout.fillWidth: true
                visible: !ponteGestos.capturando && ponteGestos.atalho !== ""
            }

            Text {
                visible: raiz.ativo && !ponteGestos.capturando && ponteGestos.atalho !== ""
                text: "✕"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMiuda
                color: areaLimpar.containsMouse ? Tema.erro : Tema.textoApagado

                MouseArea {
                    id: areaLimpar
                    anchors.fill: parent
                    anchors.margins: -6
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: ponteGestos.limparAtalho()
                }
            }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            captura.forceActiveFocus()
            ponteGestos.iniciarCaptura()
        }
    }

    Item {
        id: captura
        anchors.fill: parent
        focus: false

        Keys.onPressed: (evento) => {
            if (!ponteGestos.capturando)
                return
            evento.accepted = true
            if (evento.key === Qt.Key_Escape) {
                ponteGestos.cancelarCaptura()
                return
            }
            if (evento.isAutoRepeat)
                return
            ponteGestos.teclaPressionada(
                evento.key, evento.modifiers, evento.text, evento.nativeVirtualKey)
        }

        Keys.onReleased: (evento) => {
            if (!ponteGestos.capturando)
                return
            evento.accepted = true
            if (!evento.isAutoRepeat)
                ponteGestos.teclaSolta(evento.key)
        }

        onActiveFocusChanged: {
            if (!activeFocus && ponteGestos.capturando)
                ponteGestos.cancelarCaptura()
        }
    }
}
