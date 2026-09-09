import QtQuick
import QtQuick.Layouts
import novo

// O painel direito: câmera ao vivo, o que acabou de disparar, e a saúde.
//
// O frame chega por `QQuickImageProvider` (ui/qml/provedor_preview.py): a engine emite
// `frame_ready` como sempre, o shell guarda o QImage e incrementa um contador, e a `Image`
// abaixo relê a fonte quando o contador muda. O caminho do frame continua sendo um
// `Signal` no mesmo processo — não há cópia atravessando fronteira.
Rectangle {
    id: raiz

    color: Tema.superficie
    border.width: 1
    border.color: Tema.bordaSutil
    radius: Tema.raioGrande

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Tema.e4
        spacing: Tema.e4

        // ---------------------------------------------------------------- câmera
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: width * 9 / 16
            radius: Tema.raio
            color: "#07070a"
            border.width: 1
            border.color: shell.rodando ? Qt.rgba(0.48, 0.36, 1, 0.45) : Tema.bordaSutil
            clip: true
            Behavior on border.color { ColorAnimation { duration: 200 } }

            // A janela reduz o quadro antes de entregar; ela precisa saber para quanto.
            onWidthChanged: shell.definirTamanhoDoPreview(width, height)
            onHeightChanged: shell.definirTamanhoDoPreview(width, height)
            Component.onCompleted: shell.definirTamanhoDoPreview(width, height)

            Image {
                anchors.fill: parent
                anchors.margins: 1
                fillMode: Image.PreserveAspectFit
                cache: false
                asynchronous: false
                visible: shell.temFrame
                source: shell.temFrame ? "image://preview/" + shell.contadorDeFrames : ""
            }

            Text {
                anchors.centerIn: parent
                visible: !shell.temFrame
                text: shell.rodando ? "Iniciando câmera..." : "Câmera parada"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpo
                color: Tema.textoDesabilitado
            }

            // Latência sobre a imagem, onde o olho já está.
            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Tema.e2
                visible: shell.rodando && ponte.latencia !== ""
                implicitWidth: txtLat.implicitWidth + 14
                implicitHeight: 22
                radius: 11
                color: Qt.rgba(0.04, 0.04, 0.06, 0.82)

                Text {
                    id: txtLat
                    anchors.centerIn: parent
                    text: shell.latenciaCurta
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMicro
                    font.weight: Font.Bold
                    color: ponte.corDaLatencia
                }
            }
        }

        // ------------------------------------------------------------ último disparo
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            radius: Tema.raio
            color: shell.ultimoGesto ? Tema.okFraco : Tema.elevada
            border.width: 1
            border.color: shell.ultimoGesto ? Qt.rgba(0.2, 0.83, 0.6, 0.35) : Tema.bordaSutil
            Behavior on color { ColorAnimation { duration: 220 } }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Tema.e4
                anchors.rightMargin: Tema.e4
                spacing: Tema.e3

                Text {
                    text: shell.ultimoGesto ? "✓" : "—"
                    font.family: Tema.familia
                    font.pixelSize: 16
                    font.weight: Font.Bold
                    color: shell.ultimoGesto ? Tema.ok : Tema.textoDesabilitado
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    Text {
                        text: shell.ultimoGesto ? shell.ultimoGesto : "Nenhum gesto ainda"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        font.weight: Font.DemiBold
                        color: shell.ultimoGesto ? Tema.texto : Tema.textoApagado
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: shell.ultimaAcao !== ""
                        text: shell.ultimaAcao
                        elide: Text.ElideRight
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        color: Tema.textoApagado
                    }
                }
            }
        }

        // ------------------------------------------------------------------ saúde
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 140
            radius: Tema.raio
            color: Tema.elevada
            border.width: 1
            border.color: Tema.bordaSutil

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.e4
                spacing: Tema.e1

                Text {
                    text: "SAÚDE DO SISTEMA"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMicro
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                    color: Tema.textoApagado
                    Layout.bottomMargin: Tema.e1
                }

                // Vem do mesmo `definir_saude` que a aba Geral já recebe do health_mixin.
                Repeater {
                    model: ponte.saude

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Tema.e3
                        Layout.preferredHeight: 30

                        Rectangle {
                            width: 7
                            height: 7
                            radius: 4
                            color: modelData.cor
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            Layout.fillWidth: true
                            text: modelData.texto
                            elide: Text.ElideRight
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMiuda
                            color: Tema.textoSecundario
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.topMargin: Tema.e3
                    Layout.bottomMargin: Tema.e3
                    color: Tema.bordaSutil
                    visible: shell.disparos.length > 0
                }

                Text {
                    visible: shell.disparos.length > 0
                    text: "ÚLTIMOS DISPAROS"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMicro
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                    color: Tema.textoApagado
                    Layout.bottomMargin: Tema.e1
                }

                Repeater {
                    model: shell.disparos

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Tema.e3

                        Text {
                            text: modelData.quando
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMicro
                            color: Tema.textoDesabilitado
                            Layout.preferredWidth: 54
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.texto
                            elide: Text.ElideRight
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMiuda
                            color: Tema.textoSecundario
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
