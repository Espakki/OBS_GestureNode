import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Campo que grava uma combinação de teclas. Ver D-50.
//
// **Não traduz nada.** Recolhe os números do evento e entrega ao Python, que chama a mesma
// `ui/atalho_capturado.py` usada pela versão em Widgets. Reimplementar a tradução aqui
// perderia a defesa contra AltGr, e o teste continuaria verde porque exercita a outra tela.
//
// O `Item` com foco captura as teclas antes de qualquer atalho da janela, que é o
// necessário para gravar Ctrl+W sem fechar a aba.
Item {
    id: raiz

    property bool ativo: true

    Layout.fillWidth: true
    Layout.preferredHeight: Tema.alturaControle

    Rectangle {
        id: fundo
        anchors.fill: parent
        radius: Tema.raioPequeno
        // Durante a captura o campo fica roxo, não verde. O verde do QSS antigo (#4CAF50)
        // não tinha relação com o tema — era a única cor viva fora da paleta.
        color: ponteGestos.capturando ? Tema.destaquePressionado
             : (raiz.ativo ? Tema.controle : Tema.controleDesabilitado)
        border.width: ponteGestos.capturando ? 2 : 1
        border.color: ponteGestos.capturando ? Tema.destaqueHover
             : (area.containsMouse ? Tema.bordaHover : Tema.borda)

        Behavior on color { ColorAnimation { duration: 140 } }
        Behavior on border.color { ColorAnimation { duration: 140 } }

        Text {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: limpar.visible ? limpar.width + 16 : 12
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font.pixelSize: Tema.fonte
            text: {
                if (ponteGestos.capturando)
                    return ponteGestos.atalhoParcial || "Pressione as teclas..."
                return ponteGestos.atalho || "Clique para capturar (ESC cancela)"
            }
            color: {
                if (!raiz.ativo) return Tema.textoDesabilitado
                if (ponteGestos.capturando) return Tema.textoSobreDestaque
                return ponteGestos.atalho ? Tema.texto : Tema.textoDesabilitado
            }
        }

        // Limpar sem precisar gravar outro atalho por cima. Antes não havia como desfazer
        // um atalho a não ser apagando o campo, que era read-only.
        Text {
            id: limpar
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            visible: raiz.ativo && !ponteGestos.capturando && ponteGestos.atalho !== ""
            text: "✕"
            font.pixelSize: Tema.fonteSecundaria
            color: areaLimpar.containsMouse ? Tema.erro : Tema.textoApagado

            MouseArea {
                id: areaLimpar
                anchors.fill: parent
                anchors.margins: -6
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: ponteGestos.limparAtalho()
            }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            captura.forceActiveFocus()
            ponteGestos.iniciarCaptura()
        }
    }

    Item {
        id: captura
        anchors.fill: parent
        focus: false

        Keys.onPressed: (evento) => {
            if (!ponteGestos.capturando)
                return

            evento.accepted = true

            if (evento.key === Qt.Key_Escape) {
                ponteGestos.cancelarCaptura()
                return
            }

            if (evento.isAutoRepeat)
                return

            ponteGestos.teclaPressionada(
                evento.key, evento.modifiers, evento.text, evento.nativeVirtualKey)
        }

        Keys.onReleased: (evento) => {
            if (!ponteGestos.capturando)
                return
            evento.accepted = true
            if (!evento.isAutoRepeat)
                ponteGestos.teclaSolta(evento.key)
        }

        onActiveFocusChanged: {
            // Perder o foco no meio cancela: um campo que continuasse capturando fora de
            // vista roubaria as teclas do resto da janela.
            if (!activeFocus && ponteGestos.capturando)
                ponteGestos.cancelarCaptura()
        }
    }
}
