import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// A tela de calibrar: câmera em tamanho cheio com o diagnóstico logo abaixo.
//
// **Por que ela existe.** O painel lateral resolve "está rodando?" de relance, mas não
// resolve "meu enquadramento está bom?" — para isso é preciso ver a mão do tamanho que ela
// aparece, com o esqueleto legível. Era a queixa do dono: o preview lateral é pequeno
// demais para conferir a webcam.
//
// A separação segue o uso real: as outras telas são de **configurar** e o preview é só
// contexto; esta é de **testar**, e aqui a imagem é o assunto. O painel lateral some
// enquanto ela está aberta — mostrar a mesma câmera duas vezes na mesma tela não ajuda
// ninguém e rouba a largura de quem importa.
Item {
    id: raiz

    ColumnLayout {
        anchors.fill: parent
        spacing: Tema.e4

        // ------------------------------------------------------------- cabeçalho
        RowLayout {
            Layout.fillWidth: true
            spacing: Tema.e3

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Ao vivo"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteDisplay
                    font.weight: Font.Bold
                    color: Tema.texto
                }
                Text {
                    text: "Confira enquadramento e iluminação, e veja os gestos disparando."
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoApagado
                }
            }

            Item { Layout.fillWidth: true }

            // O que hoje está espalhado: o que a câmera está entregando, e a latência.
            Repeater {
                model: [
                    { r: shell.rodando ? "Detectando" : "Parado",
                      c: shell.rodando ? Tema.ok : Tema.neutro },
                    { r: ponte.resolucao + " · " + ponte.fps + " fps", c: Tema.neutro },
                    { r: shell.latenciaCurta || "— ms", c: ponte.corDaLatencia }
                ]

                delegate: Rectangle {
                    required property var modelData
                    implicitWidth: rot.implicitWidth + Tema.e4 * 2
                    implicitHeight: 32
                    radius: 16
                    color: Tema.elevada
                    border.width: 1
                    border.color: Tema.bordaSutil

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: Tema.e2

                        Rectangle {
                            width: 7; height: 7; radius: 4
                            color: modelData.c
                            Layout.alignment: Qt.AlignVCenter
                        }
                        Text {
                            id: rot
                            text: modelData.r
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMiuda
                            font.weight: Font.DemiBold
                            color: Tema.textoSecundario
                        }
                    }
                }
            }
        }

        // ---------------------------------------------------------------- câmera
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 220
            radius: Tema.raioGrande
            color: "#07070a"
            border.width: 1
            border.color: shell.rodando ? Qt.rgba(0.48, 0.36, 1, 0.45) : Tema.bordaSutil
            clip: true
            Behavior on border.color { ColorAnimation { duration: 200 } }

            // Esta é a maior área de preview do app, então é ela que dita para quanto a
            // janela reduz o quadro. Ver `PonteShell.definirTamanhoDoPreview`.
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

            ColumnLayout {
                anchors.centerIn: parent
                visible: !shell.temFrame
                spacing: Tema.e3

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: shell.rodando ? "Iniciando câmera..." : "Câmera parada"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteTitulo
                    color: Tema.textoApagado
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    visible: !shell.rodando
                    text: "Clique em Iniciar, no alto à direita, para ver a câmera aqui."
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoDesabilitado
                }
            }

            // O que acabou de disparar, sobre a imagem — é o que se olha ao calibrar.
            Rectangle {
                visible: shell.ultimoGesto !== ""
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: Tema.e4
                // Teto: o detalhe pode ser "cena Live, som, atalho Ctrl+Shift+F5", e sem
                // limite a pastilha cresceria até atravessar a imagem.
                implicitWidth: Math.min(linhaDisparo.implicitWidth + Tema.e4 * 2,
                                        parent.width - Tema.e4 * 2)
                height: 44
                radius: 22
                color: Qt.rgba(0.04, 0.04, 0.06, 0.86)
                border.width: 1
                border.color: Qt.rgba(0.2, 0.83, 0.6, 0.45)

                RowLayout {
                    id: linhaDisparo
                    anchors.centerIn: parent
                    spacing: Tema.e3

                    Text {
                        text: "✓"
                        font.family: Tema.familia
                        font.pixelSize: 15
                        font.weight: Font.Bold
                        color: Tema.ok
                    }
                    Text {
                        text: shell.ultimoGesto
                        elide: Text.ElideRight
                        Layout.maximumWidth: 200
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        font.weight: Font.DemiBold
                        color: Tema.texto
                    }
                    Text {
                        visible: shell.ultimaAcao !== ""
                        Layout.fillWidth: true
                        Layout.maximumWidth: 420
                        text: shell.ultimaAcao
                        elide: Text.ElideRight
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMiuda
                        color: Tema.textoApagado
                    }
                }
            }
        }

        // ----------------------------------------------------------- diagnóstico
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 196
            radius: Tema.raio
            color: "#08080b"
            border.width: 1
            border.color: Tema.bordaSutil
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.e4
                spacing: Tema.e2

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Tema.e4

                    Text {
                        text: "DIAGNÓSTICO"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    Item { Layout.fillWidth: true }

                    // A saúde numa linha, junto do log — quem está calibrando quer os dois
                    // no mesmo lugar, e não um em cada ponta da janela.
                    Repeater {
                        model: ponte.saude

                        delegate: RowLayout {
                            required property var modelData
                            spacing: Tema.e2

                            Rectangle {
                                width: 7; height: 7; radius: 4
                                color: modelData.cor
                                Layout.alignment: Qt.AlignVCenter
                            }
                            Text {
                                text: modelData.texto
                                font.family: Tema.familia
                                font.pixelSize: Tema.fonteMicro
                                color: Tema.textoApagado
                            }
                        }
                    }
                }

                ListView {
                    id: lista
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: shell.log
                    onCountChanged: positionViewAtEnd()

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Text {
                        required property string modelData
                        width: lista.width
                        text: modelData
                        font.family: "Consolas"
                        font.pixelSize: Tema.fonteMiuda
                        color: Tema.textoApagado
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
