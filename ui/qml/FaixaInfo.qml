import QtQuick
import QtQuick.Layouts

// A faixa de limite da câmera, com o tom que o D-45 definiu: paleta neutra, sem glifo de
// alerta, texto secundário. Informação de hardware não usa o vocabulário de falha.
Rectangle {
    id: raiz

    property string texto: ""

    Layout.fillWidth: true
    Layout.preferredHeight: visible ? conteudo.implicitHeight + 20 : 0

    visible: texto !== ""
    radius: Tema.raioPequeno
    color: Tema.superficie
    border.width: 1
    border.color: Tema.borda

    opacity: visible ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 150 } }

    Text {
        id: conteudo
        anchors.fill: parent
        anchors.margins: 10
        text: raiz.texto
        // 14px, como o resto do texto secundário: em 15px com fundo e borda a faixa ficava
        // parecida demais com o botão logo abaixo e podia passar por controle clicável.
        font.pixelSize: Tema.fonteSecundaria
        color: Tema.textoSecundario
        wrapMode: Text.WordWrap
        verticalAlignment: Text.AlignVCenter
    }
}
