import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// Conexão com o OBS, ligada à `PonteObs` real.
//
// Os links usam `Text.StyledText` e não `Text.RichText`: com RichText o Qt ignora
// `linkColor` e pinta o link de #0000ff — que é por que os links da interface atual saem
// azuis num tema roxo. Medido, não suposto.
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
            width: parent.width
            spacing: Tema.e5

            ColumnLayout {
                spacing: 2
                Text {
                    text: "OBS Studio"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteDisplay
                    font.weight: Font.Bold
                    color: Tema.texto
                }
                Text {
                    text: "Necessário para trocar cenas por gesto."
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoApagado
                }
            }

            // ------------------------------------------------------------ estado
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.max(72, linhaStatus.implicitHeight + Tema.e5)
                radius: Tema.raio
                color: Tema.superficie
                border.width: 1
                border.color: ponteObs.corDoStatus
                Behavior on border.color { ColorAnimation { duration: 200 } }

                RowLayout {
                    id: linhaStatus
                    anchors.fill: parent
                    anchors.leftMargin: Tema.e5
                    anchors.rightMargin: Tema.e5
                    spacing: Tema.e4

                    Rectangle {
                        Layout.alignment: Qt.AlignVCenter
                        width: 12
                        height: 12
                        radius: 6
                        color: ponteObs.corDoStatus
                        Behavior on color { ColorAnimation { duration: 200 } }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: ponteObs.status
                        wrapMode: Text.WordWrap
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        color: Tema.texto
                    }

                    BotaoAcao {
                        Layout.preferredWidth: 158
                        text: ponteObs.testando ? "Conectando..." : "Testar conexão"
                        variante: "primaria"
                        enabled: !ponteObs.testando
                        onClicked: ponteObs.testar()
                    }
                }
            }

            // ---------------------------------------------------------- credenciais
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: form.implicitHeight + Tema.e5 * 2
                radius: Tema.raio
                color: Tema.superficie
                border.width: 1
                border.color: Tema.bordaSutil

                GridLayout {
                    id: form
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: Tema.e5
                    columns: 2
                    columnSpacing: Tema.e4
                    rowSpacing: Tema.e3

                    Text {
                        text: "Host"
                        Layout.preferredWidth: 72
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        color: Tema.textoSecundario
                    }
                    CampoDeTexto {
                        text: ponteObs.host
                        placeholderText: "localhost"
                        onTextEdited: ponteObs.definirHost(text)
                    }

                    Text {
                        text: "Porta"
                        Layout.preferredWidth: 72
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        color: Tema.textoSecundario
                    }
                    CampoDeTexto {
                        text: String(ponteObs.porta)
                        placeholderText: "4455"
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: IntValidator { bottom: 1; top: 99999 }
                        onTextEdited: ponteObs.definirPorta(parseInt(text, 10) || 0)
                    }

                    Text {
                        text: "Senha"
                        Layout.preferredWidth: 72
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpo
                        color: Tema.textoSecundario
                    }
                    CampoDeTexto {
                        senha: true
                        text: ponteObs.senha
                        placeholderText: "Senha do WebSocket, se houver"
                        onTextEdited: ponteObs.definirSenha(text)
                    }
                }
            }

            // -------------------------------------------------------------- ajuda
            Text {
                text: "COMO LIGAR O SERVIDOR NO OBS"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                Repeater {
                    model: [
                        "No OBS, abra Ferramentas → Configurações do servidor WebSocket.",
                        "Marque “Ativar servidor WebSocket” e confira a porta.",
                        "Copie a senha, se houver, e cole no campo acima.",
                        "Volte aqui e clique em Testar conexão."
                    ]

                    delegate: RowLayout {
                        required property string modelData
                        required property int index
                        Layout.fillWidth: true
                        spacing: Tema.e3

                        Rectangle {
                            width: 22
                            height: 22
                            radius: 11
                            color: Tema.elevada
                            border.width: 1
                            border.color: Tema.borda
                            Layout.alignment: Qt.AlignTop

                            Text {
                                anchors.centerIn: parent
                                text: index + 1
                                font.family: Tema.familia
                                font.pixelSize: Tema.fonteMicro
                                font.weight: Font.Bold
                                color: Tema.textoSecundario
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            // Linha de leitura, nao de layout: acima de ~90 caracteres o
                            // olho perde a proxima linha.
                            Layout.maximumWidth: 720
                            text: modelData
                            wrapMode: Text.WordWrap
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMiuda
                            color: Tema.textoSecundario
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                textFormat: Text.StyledText
                linkColor: Tema.destaqueHover
                text: 'Não tem o plugin? <a href="https://github.com/obsproject/obs-websocket/releases">Baixar o OBS WebSocket</a>'
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMiuda
                color: Tema.textoApagado
                onLinkActivated: (url) => ponteObs.abrirLink(url)

                HoverHandler { cursorShape: Qt.PointingHandCursor }
            }

            Item { Layout.preferredHeight: Tema.e5 }
        }
    }
}
