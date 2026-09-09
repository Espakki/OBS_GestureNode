import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// Câmera e modo de operação, ligados à `PonteGeral` real.
//
// O modo vira cartão com a descrição visível: é a decisão mais consequente do app e na aba
// de hoje ela é um dos três toggles idênticos, com a explicação num tooltip de 500ms.
//
// "Configurações Avançadas" não existe aqui. O acordeão existia porque a coluna tinha
// 482px e não cabia tudo; com espaço, esconder resolução e FPS só acrescenta um clique.
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
            width: Math.min(parent.width, 860)
            spacing: Tema.e5

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Câmera e operação"
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteDisplay
                    font.weight: Font.Bold
                    color: Tema.texto
                }
                Text {
                    text: "Como o app se comporta quando você aperta Iniciar."
                    font.family: Tema.familia
                    font.pixelSize: Tema.fonteMiuda
                    color: Tema.textoApagado
                }
            }

            Text {
                text: "MODO DE OPERAÇÃO"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                CartaoModo {
                    glifo: "◉"
                    titulo: "Teste"
                    descricao: "Detecta e mostra os gestos no preview, mas não executa nada. Use para calibrar posição e iluminação antes de ir ao vivo."
                    selecionado: ponte.modo === "teste"
                    onEscolhido: ponte.escolherModo("teste")
                }
                CartaoModo {
                    glifo: "▶"
                    titulo: "Manual"
                    descricao: "Conecta ao OBS e executa as ações. A câmera virtual fica desligada — escolha esta se houver conflito de driver."
                    selecionado: ponte.modo === "manual"
                    onEscolhido: ponte.escolherModo("manual")
                }
                CartaoModo {
                    glifo: "⚡"
                    titulo: "Automático"
                    descricao: "Como o Manual, e ainda liga a câmera virtual ao iniciar. É o modo do uso normal."
                    selecionado: ponte.modo === "automatico"
                    onEscolhido: ponte.escolherModo("automatico")
                }
            }

            // ----------------------------------------------------------- câmera
            Text {
                Layout.topMargin: Tema.e2
                text: "DISPOSITIVO"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            ComboBox {
                id: seletor
                Layout.fillWidth: true
                implicitHeight: Tema.alturaControle
                model: ponte.cameras
                currentIndex: ponte.cameraSelecionada
                enabled: ponte.controlesHabilitados
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpo
                onActivated: (i) => ponte.escolherCamera(i)

                background: Rectangle {
                    radius: Tema.raioPequeno
                    color: seletor.enabled ? Tema.controle : Tema.controleDesabilitado
                    border.width: 1
                    border.color: seletor.activeFocus ? Tema.destaque
                                : (seletor.hovered ? Tema.bordaHover : Tema.borda)
                }

                contentItem: Text {
                    leftPadding: Tema.e3
                    rightPadding: seletor.indicator.width + Tema.e2
                    text: seletor.displayText
                    font: seletor.font
                    color: seletor.enabled ? Tema.texto : Tema.textoDesabilitado
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                indicator: Item {
                    x: seletor.width - width - Tema.e3
                    y: (seletor.height - height) / 2
                    width: 14
                    height: 14
                    rotation: seletor.popup.visible ? 180 : 0
                    Behavior on rotation { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }

                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = seletor.enabled ? Tema.textoSecundario : Tema.textoDesabilitado
                            ctx.lineWidth = 2
                            ctx.lineCap = "round"
                            ctx.lineJoin = "round"
                            ctx.beginPath()
                            ctx.moveTo(2, 5)
                            ctx.lineTo(width / 2, 10)
                            ctx.lineTo(width - 2, 5)
                            ctx.stroke()
                        }
                    }
                }

                delegate: ItemDelegate {
                    width: seletor.width
                    height: 36
                    highlighted: seletor.highlightedIndex === index
                    contentItem: Text {
                        text: modelData
                        font: seletor.font
                        color: highlighted ? Tema.textoSobreDestaque : Tema.texto
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        leftPadding: Tema.e3
                    }
                    background: Rectangle {
                        color: highlighted ? Tema.destaque : "transparent"
                    }
                }

                popup: Popup {
                    y: seletor.height + 4
                    width: seletor.width
                    implicitHeight: Math.min(contentItem.implicitHeight + 2, 280)
                    padding: 1

                    contentItem: ListView {
                        clip: true
                        implicitHeight: contentHeight
                        model: seletor.popup.visible ? seletor.delegateModel : null
                        currentIndex: seletor.highlightedIndex
                        ScrollIndicator.vertical: ScrollIndicator {}
                    }

                    background: Rectangle {
                        radius: Tema.raioPequeno
                        color: Tema.controle
                        border.width: 1
                        border.color: Tema.borda
                    }
                }
            }

            // ------------------------------------------------- resolução e fps
            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e5

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Tema.e2

                    Text {
                        text: "RESOLUÇÃO"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Tema.e2

                        Repeater {
                            model: ["480p", "720p", "1080p"]

                            delegate: BotaoAcao {
                                required property string modelData
                                Layout.fillWidth: true
                                text: modelData
                                variante: ponte.resolucao === modelData ? "primaria" : "fantasma"
                                enabled: ponte.controlesHabilitados
                                         && !ponte.resolucoesIndisponiveis.includes(modelData)
                                onClicked: ponte.escolherResolucao(modelData)
                                ToolTip.visible: hovered && !enabled
                                ToolTip.delay: 400
                                ToolTip.text: "Esta câmera não oferece " + modelData + "."
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 260
                    spacing: Tema.e2

                    Text {
                        text: "TAXA DE QUADROS"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Tema.e2

                        Repeater {
                            model: [30, 60]

                            delegate: BotaoAcao {
                                required property int modelData
                                Layout.fillWidth: true
                                text: modelData
                                variante: ponte.fps === modelData ? "primaria" : "fantasma"
                                enabled: ponte.controlesHabilitados
                                         && !ponte.fpsIndisponiveis.includes(modelData)
                                onClicked: ponte.escolherFps(modelData)
                            }
                        }
                    }
                }
            }

            // A faixa neutra do D-45: limite de hardware não usa vocabulário de falha.
            Rectangle {
                Layout.fillWidth: true
                visible: ponte.avisoDaCamera !== ""
                implicitHeight: linhaAviso.implicitHeight + Tema.e4 * 2
                radius: Tema.raio
                color: Tema.elevada
                border.width: 1
                border.color: Tema.bordaSutil

                RowLayout {
                    id: linhaAviso
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Tema.e4
                    anchors.rightMargin: Tema.e4
                    spacing: Tema.e3

                    Text {
                        Layout.fillWidth: true
                        text: ponte.avisoDaCamera
                        wrapMode: Text.WordWrap
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMiuda
                        color: Tema.textoSecundario
                    }

                    BotaoAcao {
                        visible: ponte.temRecomendacao
                        text: "Usar o recomendado"
                        variante: "fantasma"
                        Layout.preferredWidth: 180
                        onClicked: ponte.aplicarRecomendado()
                    }
                }
            }

            // ------------------------------------------------------------ mãos
            Text {
                Layout.topMargin: Tema.e2
                text: "DETECÇÃO"
                font.family: Tema.familia
                font.pixelSize: Tema.fonteMicro
                font.weight: Font.Bold
                font.letterSpacing: 0.8
                color: Tema.textoApagado
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e4

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Text {
                        text: "Detectar duas mãos"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteCorpoG
                        font.weight: Font.DemiBold
                        color: Tema.texto
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Qualquer uma das mãos aciona a mesma ação. Custa mais CPU."
                        wrapMode: Text.WordWrap
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        color: Tema.textoApagado
                    }
                }

                Rectangle {
                    implicitWidth: 44
                    implicitHeight: 24
                    radius: 12
                    color: ponte.maxMaos === 2 ? Tema.destaque : Tema.controle
                    border.width: 1
                    border.color: ponte.maxMaos === 2 ? Tema.destaque : Tema.borda
                    opacity: ponte.controlesHabilitados ? 1 : 0.5
                    Behavior on color { ColorAnimation { duration: 140 } }

                    Rectangle {
                        width: 18
                        height: 18
                        radius: 9
                        y: 3
                        x: ponte.maxMaos === 2 ? parent.width - width - 3 : 3
                        color: ponte.maxMaos === 2 ? "#ffffff" : Tema.textoApagado
                        Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
                    }

                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -4
                        enabled: ponte.controlesHabilitados
                        cursorShape: Qt.PointingHandCursor
                        onClicked: ponte.escolherMaos(ponte.maxMaos === 2 ? 1 : 2)
                    }
                }
            }

            // --------------------------------------------------------- esqueleto
            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e2

                BotaoAcao {
                    Layout.fillWidth: true
                    text: "Esqueleto no preview"
                    variante: ponte.esqueletoPreview ? "primaria" : "fantasma"
                    onClicked: ponte.alternarEsqueletoPreview(!ponte.esqueletoPreview)
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                    ToolTip.text: "Desenha o esqueleto da mão nesta janela. Não altera o que sai para o OBS."
                }

                BotaoAcao {
                    Layout.fillWidth: true
                    text: "Esqueleto na saída do OBS"
                    variante: ponte.esqueletoObs ? "primaria" : "fantasma"
                    onClicked: ponte.alternarEsqueletoObs(!ponte.esqueletoObs)
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                    ToolTip.text: "O público da live passa a ver as linhas."
                }
            }

            Item { Layout.preferredHeight: Tema.e5 }
        }
    }
}
