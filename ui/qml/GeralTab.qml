import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A aba Geral. Ver D-49.
//
// A diferença estrutural em relação à versão em Widgets não é a aparência: é que aqui a
// tela **deriva** do estado em vez de ser sincronizada com ele à mão.
//
// `checked: ponte.modo === "teste"` é uma ligação viva. Quando o estado muda, o botão
// muda — não existe um `set_mode()` que alguém precise lembrar de chamar, nem a guarda
// contra "o setChecked disparou o handler como se fosse clique" (D-41), porque marcar não
// é a mesma operação que clicar. As 43 guardas existiam para resolver um problema que
// aqui não chega a existir.
Item {
    id: raiz

    // A ponte é injetada pelo Python (ui/qml/ponte.py) como contexto.
    // Ela expõe o `EstadoApp` como propriedades observáveis.

    // O QQuickWidget limpa a cena com branco por padrão. Sem isto, o branco aparece nas
    // bordas e em qualquer área que nenhum item pinte.
    Rectangle {
        anchors.fill: parent
        color: Tema.fundo
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: Tema.espaco
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: Tema.espacoLinha

            // ---------------------------------------------------------------- modo
            LinhaDeCampo {
                rotulo: "Modo:"

                OpcaoToggle {
                    text: "Teste"
                    checked: ponte.modo === "teste"
                    onClicked: ponte.escolherModo("teste")
                    ToolTip.text: "Calibre gestos, câmera e ações sem executar nada — nenhum comando ao OBS, hotkey ou áudio."
                }
                OpcaoToggle {
                    text: "Manual"
                    checked: ponte.modo === "manual"
                    onClicked: ponte.escolherModo("manual")
                    ToolTip.text: "Conecta ao OBS e executa hotkeys e áudio, mas mantém a câmera virtual desligada."
                }
                OpcaoToggle {
                    text: "Automático"
                    checked: ponte.modo === "automatico"
                    onClicked: ponte.escolherModo("automatico")
                    ToolTip.text: "Gerencia conexão ao OBS e câmera virtual automaticamente ao iniciar."
                }
            }

            Text {
                Layout.fillWidth: true
                text: ponte.ajudaDoModo
                color: Tema.textoApagado
                font.pixelSize: Tema.fonteSecundaria
                wrapMode: Text.WordWrap
            }

            // ---------------------------------------------------------------- mãos
            LinhaDeCampo {
                rotulo: "Mãos:"

                OpcaoToggle {
                    text: "1 Mão"
                    checked: ponte.maxMaos === 1
                    onClicked: ponte.escolherMaos(1)
                    ToolTip.text: "Detecta apenas uma mão. Menor custo de CPU."
                }
                OpcaoToggle {
                    text: "2 Mãos"
                    checked: ponte.maxMaos === 2
                    onClicked: ponte.escolherMaos(2)
                    ToolTip.text: "Detecta duas mãos ao mesmo tempo. Qualquer mão aciona a mesma ação."
                }
            }

            // ------------------------------------------------------------ esqueleto
            LinhaDeCampo {
                rotulo: "Esqueleto:"

                OpcaoToggle {
                    text: "Preview"
                    checked: ponte.esqueletoPreview
                    onClicked: ponte.alternarEsqueletoPreview(!ponte.esqueletoPreview)
                    ToolTip.text: "Desenha o esqueleto da mão nesta janela, para ajustar posição e iluminação.\nNão altera o que sai para o OBS."
                }
                OpcaoToggle {
                    text: "Saída OBS"
                    checked: ponte.esqueletoObs
                    onClicked: ponte.alternarEsqueletoObs(!ponte.esqueletoObs)
                    ToolTip.text: "Desenha o esqueleto também na imagem enviada à câmera virtual — o público da live passa a ver as linhas."
                }
            }

            // -------------------------------------------------------------- câmera
            Text {
                Layout.topMargin: Tema.espaco
                text: "Configuração da câmera"
                color: Tema.tituloSecao
                font.pixelSize: Tema.fonteTitulo
                font.weight: Font.Bold
            }

            LinhaDeCampo {
                rotulo: "Dispositivo:"

                SeletorDeCamera {
                    model: ponte.cameras
                    currentIndex: ponte.cameraSelecionada
                    enabled: ponte.controlesHabilitados
                    onActivated: (indice) => ponte.escolherCamera(indice)
                }
            }

            FaixaInfo {
                texto: ponte.avisoDaCamera
            }

            Button {
                id: botaoRecomendado
                Layout.fillWidth: true
                Layout.preferredHeight: Tema.alturaControle
                visible: ponte.temRecomendacao
                text: "Usar configuração recomendada"
                font.pixelSize: Tema.fonte
                font.weight: Font.DemiBold
                onClicked: ponte.aplicarRecomendado()

                background: Rectangle {
                    radius: Tema.raio
                    color: botaoRecomendado.pressed ? Tema.controlePressionado
                         : (botaoRecomendado.hovered ? Tema.controleHover : Tema.controle)
                    border.width: 1
                    border.color: botaoRecomendado.hovered ? Tema.bordaHover : Tema.borda
                    Behavior on color { ColorAnimation { duration: 120 } }
                }
                contentItem: Text {
                    text: botaoRecomendado.text
                    font: botaoRecomendado.font
                    color: botaoRecomendado.hovered ? Tema.texto : Tema.textoApagado
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // ------------------------------------------------------------ avançado
            Button {
                id: alternarAvancado
                Layout.fillWidth: true
                Layout.preferredHeight: Tema.alturaControle
                checkable: true
                font.pixelSize: Tema.fonte
                font.weight: Font.DemiBold

                background: Rectangle {
                    radius: Tema.raio
                    color: alternarAvancado.hovered ? Tema.controleHover : Tema.controle
                    border.width: 1
                    border.color: alternarAvancado.checked ? Tema.destaque : Tema.borda
                    Behavior on border.color { ColorAnimation { duration: 120 } }
                }
                contentItem: RowLayout {
                    spacing: 6
                    Item { Layout.fillWidth: true }
                    Text {
                        text: "Configurações Avançadas"
                        font: alternarAvancado.font
                        color: alternarAvancado.checked ? Tema.texto : Tema.textoApagado
                        verticalAlignment: Text.AlignVCenter
                    }
                    Text {
                        text: "▼"
                        font.pixelSize: Tema.fonteSecundaria
                        color: alternarAvancado.checked ? Tema.texto : Tema.textoApagado
                        rotation: alternarAvancado.checked ? 180 : 0
                        Behavior on rotation { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                    }
                    Item { Layout.fillWidth: true }
                }
            }

            // O painel desliza em vez de aparecer de estalo. Em Widgets isto era
            // `setVisible(True)` e pronto — animar exigiria QPropertyAnimation na altura.
            ColumnLayout {
                id: painelAvancado
                Layout.fillWidth: true
                spacing: Tema.espacoLinha
                clip: true

                readonly property int alturaCheia: resolucaoLinha.implicitHeight
                                                 + fpsLinha.implicitHeight
                                                 + Tema.espacoLinha

                Layout.preferredHeight: alternarAvancado.checked ? alturaCheia : 0
                opacity: alternarAvancado.checked ? 1 : 0
                visible: Layout.preferredHeight > 0

                Behavior on Layout.preferredHeight {
                    NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                }
                Behavior on opacity { NumberAnimation { duration: 180 } }

                LinhaDeCampo {
                    id: resolucaoLinha
                    rotulo: "Resolução:"

                    Repeater {
                        model: ["480p", "720p", "1080p"]
                        OpcaoToggle {
                            required property string modelData
                            text: modelData
                            checked: ponte.resolucao === modelData
                            enabled: ponte.controlesHabilitados
                                     && !ponte.resolucoesIndisponiveis.includes(modelData)
                            onClicked: ponte.escolherResolucao(modelData)
                            ToolTip.text: enabled
                                ? "Define resolução do preview e da captura para " + modelData + "."
                                : "Esta câmera não oferece " + modelData + "."
                        }
                    }
                }

                LinhaDeCampo {
                    id: fpsLinha
                    rotulo: "FPS:"

                    Repeater {
                        model: [30, 60]
                        OpcaoToggle {
                            required property int modelData
                            text: modelData
                            checked: ponte.fps === modelData
                            enabled: ponte.controlesHabilitados
                                     && !ponte.fpsIndisponiveis.includes(modelData)
                            onClicked: ponte.escolherFps(modelData)
                            ToolTip.text: enabled
                                ? "Define a taxa de quadros para " + modelData + " FPS."
                                : "Esta câmera não faz " + modelData + " fps nesta resolução."
                        }
                    }
                }
            }

            // --------------------------------------------------------------- status
            Text {
                Layout.topMargin: Tema.espaco
                text: "Status do sistema"
                color: Tema.tituloSecao
                font.pixelSize: Tema.fonteTitulo
                font.weight: Font.Bold
            }

            Text {
                Layout.fillWidth: true
                text: ponte.latencia
                color: ponte.corDaLatencia
                font.pixelSize: Tema.fonteSecundaria
                Behavior on color { ColorAnimation { duration: 200 } }
            }

            Repeater {
                model: ponte.saude

                Text {
                    required property var modelData
                    Layout.fillWidth: true
                    text: "● " + modelData.texto
                    color: modelData.cor
                    font.pixelSize: Tema.fonteSecundaria
                    font.weight: Font.DemiBold
                }
            }

            Item { Layout.fillHeight: true; Layout.minimumHeight: Tema.margem }
        }
    }
}
