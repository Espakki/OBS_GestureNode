import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// A casca da interface nova.
//
// Consome as MESMAS pontes das abas de hoje (`ponte`, `ponteGestos`, `ponteObs`,
// `ponteSobre`) mais a `shell`, que cobre o que ficava fora delas: engine, preview, log e
// disparos. Nenhuma lógica de domínio mora aqui — a tela continua sendo só apresentação.
//
// Em relação à casca de Widgets:
//   4 abas horizontais         -> rail vertical
//   Iniciar/Parar/Reiniciar    -> um botão que alterna
//   estado dito em 3 lugares   -> 2 chips na barra
//   log com lugar cativo       -> gaveta de diagnóstico
Rectangle {
    id: raiz

    property int tela: 0
    property bool gaveta: false

    // Abaixo disto não cabem rail + conteúdo + painel sem espremer alguém, então o painel
    // colapsa. A quebra de 520px do `LinhaDeCampo` de hoje nunca dispara na prática: a aba
    // real mede 482px no tamanho mínimo da janela.
    readonly property bool cabePainel: width >= 1460
    property bool painelPedido: true
    // Na tela Ao vivo o painel some: ela JA e a camera em tamanho cheio, e mostrar a
    // mesma imagem duas vezes na mesma tela so tira largura de quem importa.
    readonly property bool painelVisivel: cabePainel && painelPedido && tela !== 1

    color: Tema.fundo

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ============================================================ barra superior
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Tema.alturaBarra
            color: Tema.superficie

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Tema.bordaSutil
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Tema.e5
                anchors.rightMargin: Tema.e5
                spacing: Tema.e4

                Rectangle {
                    width: 30
                    height: 30
                    radius: 9
                    color: Tema.destaque

                    Text {
                        anchors.centerIn: parent
                        text: "◈"
                        font.family: Tema.familia
                        font.pixelSize: 15
                        color: "#ffffff"
                    }
                }

                Text {
                    text: ponteSobre.nome
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteCorpoG
                    font.weight: Font.Bold
                    color: Tema.texto
                }

                Text {
                    text: ponteSobre.versao
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMicro
                    color: Tema.textoDesabilitado
                    Layout.alignment: Qt.AlignVCenter
                }

                Item { Layout.fillWidth: true }

                // O estado do sistema num lugar só.
                Chip {
                    texto: shell.estadoTexto
                    cor: shell.rodando ? Tema.ok : Tema.neutro
                    pulsando: shell.rodando
                }

                Chip {
                    texto: shell.obsTexto
                    cor: shell.obsConectado ? Tema.ok : Tema.neutro
                }

                BotaoAcao {
                    visible: raiz.cabePainel
                    text: raiz.painelPedido ? "Ocultar preview" : "Mostrar preview"
                    variante: "sutil"
                    Layout.preferredWidth: 152
                    onClicked: raiz.painelPedido = !raiz.painelPedido
                }

                Rectangle {
                    width: 1
                    height: 24
                    color: Tema.bordaSutil
                    Layout.alignment: Qt.AlignVCenter
                }

                // Um botão. "Reiniciar" saiu: é parar + iniciar, e o app já reinicia
                // sozinho quando uma troca de resolução exige.
                BotaoAcao {
                    Layout.preferredWidth: 132
                    text: shell.rodando ? "Parar" : "Iniciar"
                    glifo: shell.rodando ? "■" : "▶"
                    variante: shell.rodando ? "parar" : "primaria"
                    enabled: shell.rodando ? shell.podeParar : shell.podeIniciar
                    onClicked: shell.rodando ? shell.parar() : shell.iniciar()
                }
            }
        }

        // ============================================================ corpo
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ------------------------------------------------------------- rail
            Rectangle {
                Layout.preferredWidth: Tema.larguraRail
                Layout.fillHeight: true
                color: Tema.superficie

                Rectangle {
                    anchors.right: parent.right
                    width: 1
                    height: parent.height
                    color: Tema.bordaSutil
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Tema.e3
                    spacing: Tema.e1

                    ItemDoRail {
                        glifo: "✋"
                        rotulo: "Gestos"
                        emblema: {
                            var n = 0
                            var todos = ponteGestos.todosOsGestos
                            for (var i = 0; i < todos.length; i++)
                                if (todos[i].ativo) n++
                            return String(n)
                        }
                        selecionado: raiz.tela === 0
                        onAtivado: raiz.tela = 0
                    }
                    ItemDoRail {
                        glifo: "◉"; rotulo: "Ao vivo"
                        selecionado: raiz.tela === 1
                        onAtivado: raiz.tela = 1
                    }
                    ItemDoRail {
                        glifo: "◎"; rotulo: "Câmera"
                        selecionado: raiz.tela === 2
                        onAtivado: raiz.tela = 2
                    }
                    ItemDoRail {
                        glifo: "⚡"; rotulo: "OBS"
                        selecionado: raiz.tela === 3
                        onAtivado: raiz.tela = 3
                    }
                    ItemDoRail {
                        glifo: "ⓘ"; rotulo: "Sobre"
                        selecionado: raiz.tela === 4
                        onAtivado: raiz.tela = 4
                    }

                    Item { Layout.fillHeight: true }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.bottomMargin: Tema.e2
                        color: Tema.bordaSutil
                    }

                    ItemDoRail {
                        glifo: "≡"; rotulo: "Diagnóstico"
                        // Em "Ao vivo" o log ja esta na tela, fixo — a gaveta seria o
                        // mesmo conteudo duas vezes.
                        selecionado: raiz.gaveta && raiz.tela !== 1
                        onAtivado: {
                            if (raiz.tela === 1) raiz.tela = 0
                            raiz.gaveta = !raiz.gaveta
                        }
                    }
                }
            }

            // ---------------------------------------------------------- conteúdo
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Tema.e5
                    spacing: Tema.e4

                    StackLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentIndex: raiz.tela

                        TelaGestos {}
                        TelaAoVivo {}
                        TelaCamera {}
                        TelaObs {}
                        TelaSobre {}
                    }

                    // gaveta de diagnóstico — o log sai da tela principal
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: (raiz.gaveta && raiz.tela !== 1) ? 172 : 0
                        visible: Layout.preferredHeight > 0
                        radius: Tema.raio
                        color: "#08080b"
                        border.width: 1
                        border.color: Tema.bordaSutil
                        clip: true

                        Behavior on Layout.preferredHeight {
                            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Tema.e4
                            spacing: Tema.e2

                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: "DIAGNÓSTICO"
                                    font.family: Tema.familia
                                    font.pixelSize: Tema.fonteMicro
                                    font.weight: Font.Bold
                                    font.letterSpacing: 0.8
                                    color: Tema.textoApagado
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: shell.log.length + " linhas"
                                    font.family: Tema.familia
                                    font.pixelSize: Tema.fonteMicro
                                    color: Tema.textoDesabilitado
                                }
                            }

                            ListView {
                                id: lista
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: shell.log
                                // Segue a última linha, como o QPlainTextEdit fazia.
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

            // ----------------------------------------------------------- preview
            Item {
                Layout.preferredWidth: raiz.painelVisivel ? Tema.larguraPainel : 0
                Layout.minimumWidth: Layout.preferredWidth
                Layout.maximumWidth: Layout.preferredWidth
                Layout.fillHeight: true
                visible: raiz.painelVisivel
                clip: true

                PainelPreview {
                    anchors.fill: parent
                    anchors.topMargin: Tema.e5
                    anchors.bottomMargin: Tema.e5
                    anchors.rightMargin: Tema.e5
                }
            }
        }
    }

    // Sobreposição, declarada por último: fica acima do conteúdo.
    Onboarding {}

}
