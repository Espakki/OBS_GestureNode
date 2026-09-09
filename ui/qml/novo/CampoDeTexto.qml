import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import novo

TextField {
    id: raiz

    property bool senha: false

    Layout.fillWidth: true
    implicitHeight: Tema.alturaControle
    echoMode: senha ? TextInput.Password : TextInput.Normal
    font.family: Tema.familia
    font.pixelSize: Tema.fonteCorpo
    color: enabled ? Tema.texto : Tema.textoDesabilitado
    // O placeholder de hoje é #404040 sobre #1e1e1e — razão 1.61, praticamente invisível.
    placeholderTextColor: Tema.textoApagado
    selectionColor: Tema.destaque
    selectedTextColor: Tema.textoSobreDestaque
    leftPadding: Tema.e3
    rightPadding: Tema.e3
    // Sem isto o Tab não entra no campo — hoje nenhum controle QML do app é alcançável
    // por teclado, e eu confirmei injetando 8 Tabs sem nenhum item ganhar foco.
    activeFocusOnTab: true

    background: Rectangle {
        radius: Tema.raioPequeno
        color: raiz.enabled ? Tema.controle : Tema.controleDesabilitado
        border.width: raiz.activeFocus ? 2 : 1
        border.color: raiz.activeFocus ? Tema.destaque
                    : (raiz.hovered ? Tema.bordaHover : Tema.borda)
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }
}
