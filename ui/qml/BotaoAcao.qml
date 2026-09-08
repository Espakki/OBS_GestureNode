import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Botão de ação, em quatro variantes. Substitui os `objectName` do QSS
// (`#primary`, `#danger`, `#warning`, `#ghost`), que eram string mágica: errar o nome não
// dava erro, dava um botão cinza sem ninguém notar. Aqui `variante` só aceita o que existe.
Button {
    id: raiz

    // "primaria" | "perigo" | "alerta" | "fantasma"
    property string variante: "fantasma"

    readonly property var _paleta: ({
        "primaria": {
            base: Tema.destaque, hover: Tema.destaqueHover,
            pressionado: Tema.destaquePressionado, texto: Tema.textoSobreDestaque,
            borda: "transparent"
        },
        "perigo": {
            base: "#c0392b", hover: "#e74c3c", pressionado: "#a93226",
            texto: "#ffffff", borda: "transparent"
        },
        "alerta": {
            base: "#b7770d", hover: "#d68910", pressionado: "#9a6209",
            texto: "#ffffff", borda: "transparent"
        },
        "fantasma": {
            base: Tema.controle, hover: Tema.controleHover,
            pressionado: Tema.controlePressionado, texto: Tema.textoApagado,
            borda: Tema.borda
        }
    })

    readonly property var cores: _paleta[variante] || _paleta["fantasma"]

    Layout.fillWidth: true
    Layout.preferredHeight: Tema.alturaControle
    font.pixelSize: Tema.fonte
    font.weight: Font.DemiBold

    background: Rectangle {
        radius: Tema.raio
        color: {
            if (!raiz.enabled)
                return raiz.variante === "fantasma" ? Tema.controleDesabilitado : "#3a2a6a"
            if (raiz.pressed) return raiz.cores.pressionado
            return raiz.hovered ? raiz.cores.hover : raiz.cores.base
        }
        border.width: raiz.cores.borda === "transparent" ? 0 : 1
        border.color: raiz.hovered ? Tema.bordaHover : raiz.cores.borda

        Behavior on color { ColorAnimation { duration: 120 } }
    }

    contentItem: Text {
        text: raiz.text
        font: raiz.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        color: {
            if (!raiz.enabled) return Tema.textoDesabilitado
            if (raiz.variante === "fantasma" && raiz.hovered) return Tema.texto
            return raiz.cores.texto
        }
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    ToolTip.visible: hovered && ToolTip.text !== ""
    ToolTip.delay: 500
}
