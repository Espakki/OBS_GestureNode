import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// A aba Sobre: versão e licenças. Ver D-51.
//
// Duas obrigações num lugar só. A versão porque é o primeiro dado que qualquer suporte
// pede, e porque o app precisa saber a própria para comparar com o último release. As
// licenças porque a GPL exige que uma cópia acompanhe o binário, e "está no GitHub" não
// cumpre: quem baixou o `.exe` pode nunca ter visto o repositório.
//
// Ficar dentro do app, e não como arquivos soltos na pasta instalada, foi escolha do dono:
// cumpre a obrigação sem transformar o diretório de instalação em depósito de texto.
Item {
    id: raiz

    Rectangle {
        anchors.fill: parent
        color: Tema.fundo
    }

    PainelRolavel {
        anchors.fill: parent

        RowLayout {
            Layout.fillWidth: true
            spacing: Tema.espaco

            Text {
                text: ponteSobre.nome
                color: Tema.tituloSecao
                font.pixelSize: 22
                font.weight: Font.ExtraBold
            }

            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: rotuloVersao.implicitWidth + 16
                implicitHeight: rotuloVersao.implicitHeight + 8
                radius: 999
                color: Tema.controle
                border.width: 1
                border.color: Tema.borda

                Text {
                    id: rotuloVersao
                    anchors.centerIn: parent
                    text: "v" + ponteSobre.versao
                    color: Tema.textoSecundario
                    font.pixelSize: Tema.fonteSecundaria
                    font.weight: Font.DemiBold
                }
            }

            Item { Layout.fillWidth: true }
        }

        Text {
            Layout.fillWidth: true
            text: "Controle o OBS Studio por gestos de mão via webcam."
            color: Tema.textoApagado
            font.pixelSize: Tema.fonteSecundaria
            wrapMode: Text.WordWrap
        }

        // --- licença do próprio app ---
        Text {
            Layout.topMargin: Tema.espaco
            text: "Licença"
            color: Tema.tituloSecao
            font.pixelSize: Tema.fonteTitulo
            font.weight: Font.Bold
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: avisoGpl.implicitHeight + 24
            radius: Tema.raioPequeno
            color: Tema.superficie
            border.width: 1
            border.color: Tema.borda

            Text {
                id: avisoGpl
                anchors.fill: parent
                anchors.margins: 12
                wrapMode: Text.WordWrap
                font.pixelSize: Tema.fonteSecundaria
                color: Tema.textoSecundario
                textFormat: Text.RichText
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

        // --- terceiros ---
        Text {
            Layout.topMargin: Tema.espaco
            text: "Bibliotecas de terceiros"
            color: Tema.tituloSecao
            font.pixelSize: Tema.fonteTitulo
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true
            visible: ponteSobre.dependencias.length === 0
            text: "Catálogo de licenças não encontrado neste pacote. Rode "
                + "ferramentas/coletar_licencas.py antes de empacotar."
            color: Tema.atencao
            font.pixelSize: Tema.fonteSecundaria
            wrapMode: Text.WordWrap
        }

        // Tabela simples: nome, versão e licença. O texto completo de cada uma fica em
        // arquivo, aberto pelo botão abaixo — despejar tudo aqui seriam ~100 mil caracteres.
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
                    Layout.preferredHeight: 34
                    // Faixa alternada em vez de linha divisória: menos traço na tela para o
                    // mesmo ganho de leitura.
                    color: index % 2 === 0 ? Tema.superficie : "transparent"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: Tema.espaco

                        Text {
                            Layout.fillWidth: true
                            text: modelData.nome
                            color: Tema.texto
                            font.pixelSize: Tema.fonteSecundaria
                            elide: Text.ElideRight
                        }

                        Text {
                            text: modelData.versao
                            color: Tema.textoApagado
                            font.pixelSize: Tema.fonteSecundaria
                        }

                        Text {
                            Layout.preferredWidth: 190
                            horizontalAlignment: Text.AlignRight
                            text: modelData.licenca
                            color: Tema.textoSecundario
                            font.pixelSize: Tema.fonteSecundaria
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }

        BotaoAcao {
            Layout.topMargin: Tema.espaco
            text: "Abrir a pasta de licenças"
            enabled: ponteSobre.temLicencas
            onClicked: ponteSobre.abrirLicencas()
            ToolTip.text: "Os textos completos, um arquivo por biblioteca."
        }

        Text {
            Layout.fillWidth: true
            text: '<a href="' + ponteSobre.urlDoRepositorio + '">Código-fonte no GitHub</a>'
            textFormat: Text.RichText
            color: Tema.textoApagado
            linkColor: Tema.destaqueHover
            font.pixelSize: Tema.fonteSecundaria
            onLinkActivated: (url) => ponteSobre.abrirLink(url)

            HoverHandler { cursorShape: Qt.PointingHandCursor }
        }

        Item { Layout.fillHeight: true; Layout.minimumHeight: Tema.margem }
    }
}
