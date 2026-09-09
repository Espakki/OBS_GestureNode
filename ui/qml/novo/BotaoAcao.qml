import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

Button {
    id: raiz

    // "primaria" | "parar" | "fantasma" | "sutil"
    property string variante: "fantasma"
    property string glifo: ""

    readonly property var _p: ({
        "primaria": { base: Tema.destaque, hover: Tema.destaqueHover, press: Tema.destaquePressionado,
                      texto: Tema.textoSobreDestaque, borda: "transparent" },
        "parar":    { base: "#b3382c", hover: "#d24a3c", press: "#962e24",
                      texto: "#ffffff", borda: "transparent" },
        "fantasma": { base: Tema.controle, hover: Tema.controleHover, press: Tema.controlePressionado,
                      texto: Tema.textoSecundario, borda: Tema.borda },
        "sutil":    { base: "transparent", hover: Tema.controle, press: Tema.controlePressionado,
                      texto: Tema.textoApagado, borda: "transparent" }
    })
    readonly property var cores: _p[variante] || _p["fantasma"]

    implicitHeight: Tema.alturaControle
    padding: Tema.e4
    font.family: Tema.familia
    font.pixelSize: Tema.fonteCorpo
    font.weight: Font.DemiBold

    background: Rectangle {
        radius: Tema.raio
        color: !raiz.enabled ? Tema.controleDesabilitado
             : raiz.pressed  ? raiz.cores.press
             : raiz.hovered  ? raiz.cores.hover
                             : raiz.cores.base
        border.width: raiz.cores.borda === "transparent" ? 0 : 1
        // O desabilitado agora muda de verdade — o bug do "Parar" vermelho vivo
        // vinha de #danger vencer :disabled por especificidade no QSS.
        border.color: !raiz.enabled ? Tema.bordaDesabilitada
                    : raiz.hovered  ? Tema.bordaHover : raiz.cores.borda
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    // O rótulo é ancorado no centro e o glifo pendura à esquerda dele.
    //
    // Com `RowLayout` + dois espaçadores o que fica centrado é o CONJUNTO glifo+rótulo,
    // e o rótulo sai do meio pela largura do glifo mais o espaçamento — medi 20px de
    // desvio no botão "▶ Iniciar" (folga 56 à esquerda contra 36 à direita). O olho lê o
    // rótulo como sendo o conteúdo do botão, então ele é que precisa estar no centro.
    //
    // De quebra, `anchors.centerIn` não sofre o arredondamento que o layout tinha em
    // botão de largura ímpar (era 1px, mas some junto).
    contentItem: Item {
        implicitWidth: rotulo.implicitWidth
                     + (raiz.glifo !== "" ? glifoTexto.implicitWidth + Tema.e2 : 0)
        implicitHeight: rotulo.implicitHeight

        Text {
            id: rotulo
            anchors.centerIn: parent
            width: Math.min(implicitWidth, parent.width)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: raiz.text
            font: raiz.font
            color: !raiz.enabled ? Tema.textoDesabilitado
                 : (raiz.variante === "fantasma" && raiz.hovered) ? Tema.texto
                 : raiz.cores.texto
            Behavior on color { ColorAnimation { duration: 120 } }
        }

        Text {
            id: glifoTexto
            visible: raiz.glifo !== ""
            anchors.right: rotulo.left
            anchors.rightMargin: Tema.e2
            anchors.verticalCenter: parent.verticalCenter
            text: raiz.glifo
            font.family: Tema.familia
            font.pixelSize: Tema.fonteCorpo
            color: !raiz.enabled ? Tema.textoDesabilitado : raiz.cores.texto
        }
    }
}
