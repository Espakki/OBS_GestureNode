import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// Versão e licenças, ligadas à `PonteSobre` real. Ver D-51.
Item {
    id: raiz

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: coluna.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: coluna
            width: Math.min(parent.width, 820)
            spacing: Tema.e5

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                Text {
                    text: ponteSobre.nome
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteDisplay
                    font.weight: Font.Bold
                    color: Tema.texto
                }

                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    implicitWidth: rotuloVersao.implicitWidth + 16
                    implicitHeight: 26
                    radius: 13
                    color: Tema.elevada
                    border.width: 1
                    border.color: Tema.bordaSutil

                    Text {
                        id: rotuloVersao
                        anchors.centerIn: parent
                        text: "v" + ponteSobre.versao
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMiuda
                        font.weight: Font.DemiBold
                        color: Tema.textoSecundario
                    }
                }

                Item { Layout.fillWidth: true }
            }

            Text {
                Layout.fillWidth: true
                text: "Controle o OBS Studio por gestos de mão via webcam."
                wrapMode: Text.WordWrap
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMiuda
                color: Tema.textoApagado
            }

            Text {
                Layout.topMargin: Tema.e2
                text: "LICENÇA"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: avisoGpl.implicitHeight + Tema.e5 * 2
                radius: Tema.raio
                color: Tema.superficie
                border.width: 1
                border.color: Tema.bordaSutil

                Text {
                    id: avisoGpl
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: Tema.e5
                    wrapMode: Text.WordWrap
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoSecundario
                    textFormat: Text.StyledText
                    linkColor: Tema.destaqueHover
                    text: "Este programa é software livre, sob a <b>GPL-3.0</b>. Você pode "
                        + "redistribuí-lo e modificá-lo nos termos da licença.<br><br>"
                        + "Distribuído SEM NENHUMA GARANTIA — sem sequer a garantia implícita "
                        + "de comercialização ou adequação a um propósito específico.<br><br>"
                        + '<a href="https://www.gnu.org/licenses/gpl-3.0.html">Texto completo da GPL-3.0</a>'
                    onLinkActivated: (url) => ponteSobre.abrirLink(url)

                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                }
            }

            Text {
                Layout.topMargin: Tema.e2
                text: "BIBLIOTECAS DE TERCEIROS"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            Text {
                Layout.fillWidth: true
                visible: ponteSobre.dependencias.length === 0
                text: "Catálogo de licenças não encontrado neste pacote. Rode "
                    + "ferramentas/coletar_licencas.py antes de empacotar."
                wrapMode: Text.WordWrap
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMiuda
                color: Tema.atencao
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                visible: ponteSobre.dependencias.length > 0

                Repeater {
                    model: ponteSobre.dependencias

                    delegate: Rectangle {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        color: index % 2 === 0 ? Tema.superficie : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Tema.e4
                            anchors.rightMargin: Tema.e4
                            spacing: Tema.e4

                            Text {
                                Layout.fillWidth: true
                                text: modelData.nome
                                elide: Text.ElideRight
                                font.family: Tema.familia
                                font.pixelSize: Tema.fonteMiuda
                                color: Tema.texto
                            }
                            Text {
                                text: modelData.versao
                                font.family: Tema.familia
                                font.pixelSize: Tema.fonteMiuda
                                color: Tema.textoApagado
                            }
                            Text {
                                Layout.preferredWidth: 190
                                horizontalAlignment: Text.AlignRight
                                text: modelData.licenca
                                elide: Text.ElideRight
                                font.family: Tema.familia
                                font.pixelSize: Tema.fonteMiuda
                                color: Tema.textoSecundario
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                BotaoAcao {
                    Layout.preferredWidth: 220
                    text: "Abrir a pasta de licenças"
                    variante: "fantasma"
                    enabled: ponteSobre.temLicencas
                    onClicked: ponteSobre.abrirLicencas()
                }

                Item { Layout.fillWidth: true }
            }

            Text {
                Layout.fillWidth: true
                textFormat: Text.StyledText
                linkColor: Tema.destaqueHover
                text: '<a href="' + ponteSobre.urlDoRepositorio + '">Código-fonte no GitHub</a>'
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMiuda
                color: Tema.textoApagado
                onLinkActivated: (url) => ponteSobre.abrirLink(url)

                HoverHandler { cursorShape: Qt.PointingHandCursor }
            }

            Item { Layout.preferredHeight: Tema.e5 }
        }
    }
}
