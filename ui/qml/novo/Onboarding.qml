import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// O onboarding como sobreposição da própria janela, não como diálogo separado.
//
// O de Widgets era um `QDialog` modal de 540x360 aberto por `main.py` antes de a janela
// ganhar foco: ele cobria a interface que estava explicando. Aqui a janela continua
// visível atrás — o usuário lê "abra Câmera no menu à esquerda" com o menu à vista.
Item {
    id: raiz

    anchors.fill: parent
    visible: onboarding.visivel
    z: 100

    // Escurece o fundo e come os cliques, para o onboarding ser modal sem ser outra janela.
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.62

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            // Sem `onClicked` de propósito: clicar fora não fecha. Fechar é decisão
            // explícita — "Pular" existe para isso, e um clique perdido não deve gastá-la.
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width - Tema.e6 * 2, 620)
        height: Math.min(parent.height - Tema.e6 * 2, 460)
        radius: Tema.raioGrande
        color: Tema.superficie
        border.width: 1
        border.color: Tema.borda

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Tema.e6
            spacing: Tema.e5

            // ------------------------------------------------------------ topo
            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e4

                Rectangle {
                    width: 44
                    height: 44
                    radius: Tema.raio
                    color: Tema.destaqueFraco
                    border.width: 1
                    border.color: Tema.destaque

                    Text {
                        anchors.centerIn: parent
                        text: onboarding.glifo
                        font.family: Tema.familia
                        font.pixelSize: 20
                        color: Tema.destaqueHover
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "PASSO " + (onboarding.passo + 1) + " DE " + onboarding.total
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    Text {
                        Layout.fillWidth: true
                        text: onboarding.titulo
                        elide: Text.ElideRight
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteDisplay
                        font.weight: Font.Bold
                        color: Tema.texto
                    }
                }

                BotaoAcao {
                    Layout.preferredWidth: 86
                    Layout.alignment: Qt.AlignTop
                    text: "Pular"
                    variante: "sutil"
                    onClicked: onboarding.pular()
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Tema.bordaSutil
            }

            // ----------------------------------------------------------- corpo
            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: corpo.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                Text {
                    id: corpo
                    width: parent.width
                    text: onboarding.corpo
                    // StyledText, não RichText: é o que faz o <b> valer sem o Qt trazer a
                    // folha de estilo dele junto.
                    textFormat: Text.StyledText
                    wrapMode: Text.WordWrap
                    lineHeight: 1.35
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteCorpoG
                    color: Tema.textoSecundario
                }
            }

            // ----------------------------------------------------------- rodapé
            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                BotaoAcao {
                    Layout.preferredWidth: 118
                    text: "Anterior"
                    variante: "fantasma"
                    enabled: onboarding.temAnterior
                    onClicked: onboarding.voltar()
                }

                Item { Layout.fillWidth: true }

                // Os pontos também navegam: quem quer reler o passo 2 não precisa
                // percorrer o caminho de volta.
                RowLayout {
                    spacing: Tema.e2

                    Repeater {
                        model: onboarding.total

                        delegate: Rectangle {
                            required property int index
                            width: index === onboarding.passo ? 20 : 8
                            height: 8
                            radius: 4
                            color: index === onboarding.passo ? Tema.destaque : Tema.controle
                            border.width: 1
                            border.color: index === onboarding.passo ? Tema.destaque : Tema.borda

                            Behavior on width { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                            Behavior on color { ColorAnimation { duration: 150 } }

                            MouseArea {
                                anchors.fill: parent
                                anchors.margins: -6
                                cursorShape: Qt.PointingHandCursor
                                onClicked: onboarding.irPara(index)
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                BotaoAcao {
                    Layout.preferredWidth: 148
                    text: onboarding.ehUltimo ? "Começar" : "Próximo"
                    glifo: onboarding.ehUltimo ? "▶" : ""
                    variante: "primaria"
                    onClicked: onboarding.avancar()
                }
            }
        }
    }

    // Setas e Esc funcionam — é a única parte do app hoje com navegação por teclado.
    focus: onboarding.visivel
    Keys.onPressed: (evento) => {
        if (evento.key === Qt.Key_Right || evento.key === Qt.Key_Return || evento.key === Qt.Key_Enter) {
            onboarding.avancar()
            evento.accepted = true
        } else if (evento.key === Qt.Key_Left) {
            onboarding.voltar()
            evento.accepted = true
        } else if (evento.key === Qt.Key_Escape) {
            onboarding.pular()
            evento.accepted = true
        }
    }
}
