import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// Campo de texto do tema. Equivale ao `QLineEdit` estilizado por QSS.
//
// O foco aqui é **visível**: a borda vira roxa e o traço engorda. No QSS isso existia
// (`QLineEdit:focus`), mas a espessura não podia mudar sem o layout pular, porque a borda
// entra no cálculo de tamanho do widget. Aqui a borda é do retângulo de fundo e não afeta
// o layout — então dá para engordar sem nada se mexer.
TextField {
    id: raiz

    property bool senha: false

    Layout.fillWidth: true
    Layout.preferredHeight: Tema.alturaControle

    echoMode: senha ? TextInput.Password : TextInput.Normal
    font.pixelSize: Tema.fonte
    color: enabled ? Tema.texto : Tema.textoDesabilitado
    placeholderTextColor: Tema.textoDesabilitado
    selectionColor: Tema.destaque
    selectedTextColor: Tema.textoSobreDestaque
    leftPadding: 12
    rightPadding: 12

    background: Rectangle {
        radius: Tema.raioPequeno
        color: raiz.enabled ? Tema.controle : Tema.controleDesabilitado
        border.width: raiz.activeFocus ? 2 : 1
        border.color: raiz.activeFocus ? Tema.destaque
                                       : (raiz.hovered ? Tema.bordaHover : Tema.borda)

        Behavior on border.color { ColorAnimation { duration: 120 } }
    }
}
