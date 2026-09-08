import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A aba OBS. Ver D-49.
//
// Aqui os campos são **graváveis** por ligação, ao contrário da aba Geral. A diferença não
// é estilo: host, porta e senha só guardam valor — nenhum deles reinicia câmera, pede
// confirmação ou dispara probe. Onde a escrita não tem consequência, o caminho curto é o
// certo; onde tem (o número de mãos, por exemplo), continua passando por um Slot no Python.
Item {
    id: raiz

    Rectangle {
        anchors.fill: parent
        color: Tema.fundo
    }

    PainelRolavel {
        anchors.fill: parent

        Text {
            text: "Conexão OBS"
            color: Tema.tituloSecao
            font.pixelSize: 22
            font.weight: Font.ExtraBold
        }

        LinhaDeCampo {
            rotulo: "Host:"

            CampoDeTexto {
                text: ponteObs.host
                placeholderText: "Ex: localhost"
                onTextEdited: ponteObs.definirHost(text)
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: "Host do OBS WebSocket. Use localhost quando o OBS está no mesmo PC."
            }
        }

        LinhaDeCampo {
            rotulo: "Porta:"

            SpinBox {
                id: porta
                Layout.fillWidth: true
                Layout.preferredHeight: Tema.alturaControle
                from: 1
                to: 99999
                editable: true
                value: ponteObs.porta
                onValueModified: ponteObs.definirPorta(value)
                font.pixelSize: Tema.fonte

                // Sem separador de milhar: o padrão do locale mostrava a porta 4455 como
                // "4.455", que não é como ninguém escreve porta — e nem o que o OBS aceita
                // se o usuário copiar de volta.
                textFromValue: function (valor, locale) { return String(valor) }
                valueFromText: function (texto, locale) { return parseInt(texto, 10) || 0 }

                contentItem: TextInput {
                    text: porta.textFromValue(porta.value, porta.locale)
                    font: porta.font
                    color: Tema.texto
                    selectionColor: Tema.destaque
                    selectedTextColor: Tema.textoSobreDestaque
                    horizontalAlignment: Qt.AlignHCenter
                    verticalAlignment: Qt.AlignVCenter
                    readOnly: !porta.editable
                    validator: porta.validator
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                }

                background: Rectangle {
                    radius: Tema.raioPequeno
                    color: Tema.controle
                    border.width: porta.activeFocus ? 2 : 1
                    border.color: porta.activeFocus ? Tema.destaque : Tema.borda
                }

                up.indicator: Rectangle {
                    x: porta.width - width - 4
                    y: 4
                    height: porta.height / 2 - 5
                    width: 26
                    radius: 4
                    color: porta.up.hovered ? Tema.controleHover : "transparent"
                    Text {
                        anchors.centerIn: parent
                        text: "+"
                        color: Tema.textoSecundario
                        font.pixelSize: Tema.fonte
                    }
                }

                down.indicator: Rectangle {
                    x: porta.width - width - 4
                    y: porta.height / 2 + 1
                    height: porta.height / 2 - 5
                    width: 26
                    radius: 4
                    color: porta.down.hovered ? Tema.controleHover : "transparent"
                    Text {
                        anchors.centerIn: parent
                        text: "−"
                        color: Tema.textoSecundario
                        font.pixelSize: Tema.fonte
                    }
                }
            }
        }

        LinhaDeCampo {
            rotulo: "Senha:"

            CampoDeTexto {
                senha: true
                text: ponteObs.senha
                placeholderText: "Senha do OBS WebSocket"
                onTextEdited: ponteObs.definirSenha(text)
            }
        }

        BotaoAcao {
            text: ponteObs.testando ? "Conectando..." : "Testar conexão"
            variante: "primaria"
            enabled: !ponteObs.testando
            onClicked: ponteObs.testar()
            ToolTip.text: "Verifica se host, porta e senha conseguem conectar ao OBS."
        }

        // O status ganhou forma de bloco, com a cor dizendo o resultado antes da leitura.
        // Antes era um QLabel solto, com a mesma aparência para "conectado" e "falhou".
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: linhaStatus.implicitHeight + 20
            radius: Tema.raioPequeno
            color: Tema.superficie
            border.width: 1
            border.color: ponteObs.corDoStatus
            Behavior on border.color { ColorAnimation { duration: 200 } }

            RowLayout {
                id: linhaStatus
                anchors.fill: parent
                anchors.margins: 10
                spacing: Tema.espaco

                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    width: 10
                    height: 10
                    radius: 5
                    color: ponteObs.corDoStatus
                    Behavior on color { ColorAnimation { duration: 200 } }
                }

                Text {
                    Layout.fillWidth: true
                    text: ponteObs.status
                    color: Tema.texto
                    font.pixelSize: Tema.fonteSecundaria
                    wrapMode: Text.WordWrap
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: Tema.espaco
            text: "Conecte o controlador ao OBS para trocar cenas por gesto. É preciso ter o "
                + "plugin OBS WebSocket instalado e o servidor ligado em "
                + "Ferramentas → Configurações do WebSocket."
            color: Tema.textoApagado
            font.pixelSize: Tema.fonteSecundaria
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            text: '<a href="https://github.com/obsproject/obs-websocket/releases">Baixar o OBS WebSocket</a>'
            textFormat: Text.RichText
            color: Tema.textoApagado
            linkColor: Tema.destaqueHover
            font.pixelSize: Tema.fonteSecundaria
            wrapMode: Text.WordWrap
            onLinkActivated: (url) => ponteObs.abrirLink(url)

            HoverHandler {
                cursorShape: Qt.PointingHandCursor
            }
        }

        Item { Layout.fillHeight: true; Layout.minimumHeight: Tema.margem }
    }
}
