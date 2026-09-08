import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A aba Gestos. Ver D-49.
//
// A grade usa `Flow`, que reflui sozinho conforme a largura. A versão em Widgets fazia
// isso à mão — `_relayout_buttons()` calculava as colunas dividindo a largura do viewport
// por 120 e reposicionava cada botão no `QGridLayout`, chamado de `resizeEvent` e de um
// `QTimer.singleShot(10)` no `showEvent` porque a geometria ainda não existia na hora.
// Aqui é uma propriedade.
Item {
    id: raiz

    Rectangle {
        anchors.fill: parent
        color: Tema.fundo
    }

    PainelRolavel {
        anchors.fill: parent

        // ------------------------------------------------------------------ grade
        RowLayout {
            Layout.fillWidth: true
            spacing: Tema.espaco

            Text {
                Layout.fillWidth: true
                text: "Gestos ativos"
                color: Tema.tituloSecao
                font.pixelSize: Tema.fonteTitulo
                font.weight: Font.Bold
            }

            BotaoAcao {
                Layout.fillWidth: false
                Layout.preferredWidth: 160
                text: "Escolher gestos"
                onClicked: ponteGestos.escolherGestos()
                ToolTip.text: "Escolhe quais gestos aparecem nesta grade."
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: Tema.espaco

            Repeater {
                model: ponteGestos.gestos

                delegate: Item {
                    required property var modelData

                    width: 112
                    height: 132

                    readonly property bool selecionado: modelData.nome === ponteGestos.gestoAtual

                    Rectangle {
                        id: cartao
                        anchors.fill: parent
                        radius: Tema.raio
                        color: parent.selecionado ? "#1b1428"
                             : (areaGesto.containsMouse ? Tema.controleHover : Tema.controle)
                        border.width: parent.selecionado ? 2 : 1
                        border.color: parent.selecionado ? Tema.destaque
                             : (areaGesto.containsMouse ? Tema.bordaHover : Tema.borda)

                        Behavior on color { ColorAnimation { duration: 120 } }
                        Behavior on border.color { ColorAnimation { duration: 120 } }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Image {
                                Layout.alignment: Qt.AlignHCenter
                                source: modelData.icone
                                sourceSize.width: 56
                                sourceSize.height: 56
                                fillMode: Image.PreserveAspectFit
                                // Ícone ausente não pode deixar um buraco: o cartão
                                // continua clicável e o nome ainda identifica o gesto.
                                visible: status === Image.Ready
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.nome
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                                font.pixelSize: Tema.fonteSecundaria
                                font.weight: Font.DemiBold
                                color: parent.parent.selecionado ? Tema.texto : Tema.textoSecundario
                            }
                        }
                    }

                    MouseArea {
                        id: areaGesto
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: ponteGestos.selecionarGesto(modelData.nome)
                    }
                }
            }
        }

        // Estado vazio: antes a grade simplesmente ficava em branco, sem dizer o que fazer.
        Text {
            Layout.fillWidth: true
            visible: ponteGestos.gestos.length === 0
            text: "Nenhum gesto ativo. Use “Escolher gestos” para adicionar."
            color: Tema.textoApagado
            font.pixelSize: Tema.fonteSecundaria
            wrapMode: Text.WordWrap
        }

        // ---------------------------------------------------------------- editor
        Text {
            Layout.topMargin: Tema.espaco
            Layout.fillWidth: true
            text: ponteGestos.gestoAtual
                ? "Configurando: " + ponteGestos.gestoAtual
                : "Selecione um gesto"
            color: Tema.tituloSecao
            font.pixelSize: Tema.fonteTitulo
            font.weight: Font.Bold
            elide: Text.ElideRight
        }

        LinhaDeCampo {
            rotulo: "Segurar por:"
            visible: ponteGestos.gestoAtual !== ""

            Deslizante {
                valor: ponteGestos.holdTime
                minimo: 0.5
                maximo: 5.0
                passo: 0.1
                onEditado: (novo) => ponteGestos.definirHold(novo)
            }
        }

        LinhaDeCampo {
            rotulo: "Intervalo:"
            visible: ponteGestos.gestoAtual !== ""

            Deslizante {
                valor: ponteGestos.cooldown
                minimo: 2.0
                maximo: 20.0
                passo: 0.1
                onEditado: (novo) => ponteGestos.definirCooldown(novo)
            }
        }

        // --- cena ---
        ColumnLayout {
            Layout.fillWidth: true
            visible: ponteGestos.gestoAtual !== ""
            spacing: 6

            Interruptor {
                text: "Trocar cena no OBS"
                checked: ponteGestos.usaCena
                onToggled: ponteGestos.alternarCena(checked)
            }

            CampoDeTexto {
                text: ponteGestos.cena
                enabled: ponteGestos.usaCena
                placeholderText: "Nome exato da cena no OBS"
                onTextEdited: ponteGestos.definirCena(text)
            }
        }

        // --- som ---
        ColumnLayout {
            Layout.fillWidth: true
            visible: ponteGestos.gestoAtual !== ""
            spacing: 6

            Interruptor {
                text: "Tocar um som"
                checked: ponteGestos.usaSom
                onToggled: ponteGestos.alternarSom(checked)
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.espaco

                CampoDeTexto {
                    text: ponteGestos.arquivoDeSom
                    enabled: ponteGestos.usaSom
                    placeholderText: "Caminho do arquivo de áudio"
                    onTextEdited: ponteGestos.definirArquivoDeSom(text)
                }

                BotaoAcao {
                    Layout.fillWidth: false
                    Layout.preferredWidth: 110
                    text: "Procurar"
                    enabled: ponteGestos.usaSom
                    onClicked: ponteGestos.procurarSom()
                }
            }

            Text {
                Layout.fillWidth: true
                visible: ponteGestos.usaSom && ponteGestos.erroDoSom !== ""
                text: ponteGestos.erroDoSom
                color: Tema.atencao
                font.pixelSize: Tema.fonteSecundaria
                wrapMode: Text.WordWrap
            }
        }

        // --- atalho ---
        ColumnLayout {
            Layout.fillWidth: true
            visible: ponteGestos.gestoAtual !== ""
            spacing: 6

            Interruptor {
                text: "Enviar um atalho de teclado"
                checked: ponteGestos.usaAtalho
                onToggled: ponteGestos.alternarAtalho(checked)
            }

            CapturaDeAtalho {
                ativo: ponteGestos.usaAtalho
            }
        }

        Item { Layout.fillHeight: true; Layout.minimumHeight: Tema.margem }
    }
}
