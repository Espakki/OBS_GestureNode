import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

// A tela de Gestos da interface nova, ligada à `PonteGestos` real.
//
// Duas diferenças de estrutura em relação à aba de hoje:
//
// - A grade lista os doze gestos com interruptor no cartão, então o diálogo modal
//   `open_gesture_selector_dialog` não é chamado aqui.
// - O editor fica fixo ao lado da grade, em vez de empilhado abaixo dela — escolher e
//   editar deixam de exigir rolagem entre um e outro.
Item {
    id: raiz

    // Lado a lado só quando cabem os dois; abaixo disso o editor vai para baixo.
    readonly property bool estreito: width < 860

    // Empilhado, a página inteira rola. Antes cada metade tinha rolagem própria e as
    // duas disputavam a altura — com 460px fixos no editor, a grade era espremida a zero
    // e SUMIA a 960x600. Aqui só o Flickable de fora rola, e cada metade ocupa o que
    // precisa.
    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: raiz.estreito ? conteudo.implicitHeight : height
        interactive: raiz.estreito
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar { policy: raiz.estreito ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }

    GridLayout {
        width: parent.width
        height: raiz.estreito ? implicitHeight : parent.height
        id: conteudo
        columns: raiz.estreito ? 1 : 2
        columnSpacing: Tema.e5
        rowSpacing: Tema.e5

        // ------------------------------------------------------------------ grade
        ColumnLayout {
            id: colunaGrade
            Layout.fillWidth: true
            Layout.fillHeight: !raiz.estreito
            // Empilhada, a grade pede a altura do conteúdo em vez de brigar pela sobra.
            Layout.preferredHeight: raiz.estreito ? implicitHeight : -1
            spacing: Tema.e4

            RowLayout {
                Layout.fillWidth: true
                spacing: Tema.e3

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: "Gestos"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteDisplay
                        font.weight: Font.Bold
                        color: Tema.texto
                    }
                    Text {
                        text: "Ligue o que quer usar e clique para configurar a ação."
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMiuda
                        color: Tema.textoApagado
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    implicitWidth: contagem.implicitWidth + Tema.e4 * 2
                    implicitHeight: 30
                    radius: 15
                    color: Tema.elevada
                    border.width: 1
                    border.color: Tema.bordaSutil

                    Text {
                        id: contagem
                        anchors.centerIn: parent
                        text: {
                            var n = 0
                            var todos = ponteGestos.todosOsGestos
                            for (var i = 0; i < todos.length; i++)
                                if (todos[i].ativo) n++
                            return n + " de " + todos.length + " ativos"
                        }
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMiuda
                        font.weight: Font.DemiBold
                        color: Tema.textoSecundario
                    }
                }
            }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: !raiz.estreito
                Layout.preferredHeight: raiz.estreito ? grade.implicitHeight : -1
                contentWidth: width
                contentHeight: grade.implicitHeight
                interactive: !raiz.estreito
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    policy: raiz.estreito ? ScrollBar.AlwaysOff : ScrollBar.AsNeeded
                }

                Flow {
                    id: grade
                    width: parent.width
                    spacing: Tema.e3

                    Repeater {
                        model: ponteGestos.todosOsGestos

                        delegate: CartaoGesto {
                            required property var modelData

                            nome: modelData.nome
                            icone: modelData.icone
                            ativo: modelData.ativo
                            resumo: modelData.resumo
                            selecionado: modelData.nome === ponteGestos.gestoAtual

                            onEscolhido: ponteGestos.selecionarGesto(modelData.nome)
                            onAlternado: (ligado) => ponteGestos.alternarAtivo(modelData.nome, ligado)
                        }
                    }
                }
            }
        }

        // ----------------------------------------------------------------- editor
        Rectangle {
            Layout.preferredWidth: raiz.estreito ? -1 : 392
            Layout.fillWidth: raiz.estreito
            Layout.fillHeight: !raiz.estreito
            Layout.preferredHeight: raiz.estreito
                ? (ponteGestos.gestoAtual === "" ? 120 : colunaEditor.implicitHeight + Tema.e5 * 2)
                : -1
            radius: Tema.raioGrande
            color: Tema.superficie
            border.width: 1
            border.color: Tema.bordaSutil

            Text {
                anchors.centerIn: parent
                width: parent.width - Tema.e6 * 2
                visible: ponteGestos.gestoAtual === ""
                text: "Selecione um gesto na grade para configurar o que ele faz."
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                font.family: Tema.familia
                font.pixelSize: Tema.fonteCorpo
                color: Tema.textoApagado
            }

            Flickable {
                anchors.fill: parent
                anchors.margins: Tema.e5
                visible: ponteGestos.gestoAtual !== ""
                contentWidth: width
                contentHeight: colunaEditor.implicitHeight
                interactive: !raiz.estreito
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    policy: raiz.estreito ? ScrollBar.AlwaysOff : ScrollBar.AsNeeded
                }

                ColumnLayout {
                    id: colunaEditor
                    width: parent.width
                    spacing: Tema.e4

                    Text {
                        Layout.fillWidth: true
                        text: ponteGestos.gestoAtual
                        elide: Text.ElideRight
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteTitulo
                        font.weight: Font.Bold
                        color: Tema.texto
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: Tema.bordaSutil
                    }

                    Text {
                        text: "TEMPO"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    Deslizante {
                        rotulo: "Segurar por"
                        valor: ponteGestos.holdTime
                        minimo: 0.5
                        maximo: 5.0
                        passo: 0.1
                        onEditado: (novo) => ponteGestos.definirHold(novo)
                        faixas: [
                            { ate: 0.9, texto: "Rápido — pode disparar sozinho enquanto você fala", cor: Tema.atencao },
                            { ate: 2.0, texto: "Equilibrado — recomendado para uso ao vivo", cor: Tema.ok },
                            { ate: 5.0, texto: "Lento — seguro, mas parece que travou", cor: Tema.atencao }
                        ]
                    }

                    Deslizante {
                        rotulo: "Intervalo entre disparos"
                        valor: ponteGestos.cooldown
                        minimo: 2.0
                        maximo: 20.0
                        passo: 0.1
                        onEditado: (novo) => ponteGestos.definirCooldown(novo)
                        faixas: [
                            { ate: 3.0, texto: "Curto — repete rápido se a mão continuar no quadro", cor: Tema.atencao },
                            { ate: 8.0, texto: "Equilibrado", cor: Tema.ok },
                            { ate: 20.0, texto: "Longo — evita repetição, responde devagar", cor: Tema.neutro }
                        ]
                    }

                    Text {
                        Layout.topMargin: Tema.e2
                        text: "AÇÕES"
                        font.family: Tema.familia
                        font.pixelSize: Tema.fonteMicro
                        font.weight: Font.Bold
                        font.letterSpacing: 0.8
                        color: Tema.textoApagado
                    }

                    CartaoAcao {
                        titulo: "Trocar cena no OBS"
                        glifo: "▣"
                        explicacao: "Muda para uma cena pelo nome exato."
                        ligado: ponteGestos.usaCena
                        onAlternado: (v) => ponteGestos.alternarCena(v)

                        CampoDeTexto {
                            text: ponteGestos.cena
                            placeholderText: "Nome exato da cena no OBS"
                            onTextEdited: ponteGestos.definirCena(text)
                        }
                    }

                    CartaoAcao {
                        titulo: "Tocar um som"
                        glifo: "♪"
                        explicacao: "Reproduz um arquivo de áudio local."
                        ligado: ponteGestos.usaSom
                        onAlternado: (v) => ponteGestos.alternarSom(v)

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Tema.e2

                            CampoDeTexto {
                                text: ponteGestos.arquivoDeSom
                                placeholderText: "Caminho do arquivo de áudio"
                                onTextEdited: ponteGestos.definirArquivoDeSom(text)
                            }

                            BotaoAcao {
                                text: "Procurar"
                                variante: "fantasma"
                                Layout.preferredWidth: 108
                                onClicked: ponteGestos.procurarSom()
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: ponteGestos.erroDoSom !== ""
                            text: ponteGestos.erroDoSom
                            wrapMode: Text.WordWrap
                            font.family: Tema.familia
                            font.pixelSize: Tema.fonteMicro
                            color: Tema.atencao
                        }
                    }

                    CartaoAcao {
                        titulo: "Enviar atalho de teclado"
                        glifo: "⌨"
                        explicacao: "Dispara uma combinação para o app em foco."
                        ligado: ponteGestos.usaAtalho
                        onAlternado: (v) => ponteGestos.alternarAtalho(v)

                        CapturaDeAtalho {
                            ativo: ponteGestos.usaAtalho
                        }
                    }

                    Item { Layout.preferredHeight: Tema.e3 }
                }
            }
        }
    }
    }

}
