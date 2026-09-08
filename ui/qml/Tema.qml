pragma Singleton
import QtQuick

// Os tokens do tema Streamer Dark, num lugar só. Ver D-49.
//
// No QSS isto era impossível: a linguagem não tem variável, então as mesmas cores estavam
// escritas literalmente em `ui/styles.py` e em mais quatro arquivos que chamavam
// `setStyleSheet` inline — inclusive um verde `#4CAF50` no campo de atalho que não tinha
// relação nenhuma com o roxo do resto. Aqui trocar uma cor é trocar uma linha.
QtObject {
    // --- superfícies, do fundo para a frente ---
    readonly property color fundo: "#0d0d0d"
    readonly property color superficie: "#161616"
    readonly property color controle: "#1e1e1e"
    readonly property color controleHover: "#252525"
    readonly property color controlePressionado: "#181818"
    readonly property color controleDesabilitado: "#141414"

    // --- traços ---
    readonly property color borda: "#2d2d2d"
    readonly property color bordaHover: "#404040"
    readonly property color bordaDesabilitada: "#1e1e1e"

    // --- texto ---
    readonly property color texto: "#f0f0f0"
    readonly property color textoSecundario: "#909090"
    readonly property color textoApagado: "#707070"
    readonly property color textoDesabilitado: "#404040"
    readonly property color textoSobreDestaque: "#ffffff"

    // --- destaque ---
    readonly property color destaque: "#7c4dff"
    readonly property color destaqueHover: "#9965ff"
    readonly property color destaquePressionado: "#6a3de0"
    readonly property color tituloSecao: "#c0b0ff"

    // --- severidade, a mesma escala do painel de saúde ---
    readonly property color ok: "#22c55e"
    readonly property color atencao: "#f59e0b"
    readonly property color erro: "#ef4444"
    readonly property color neutro: "#94a3b8"

    // --- métrica ---
    readonly property int raio: 8
    readonly property int raioPequeno: 6
    readonly property int alturaControle: 38
    readonly property int espaco: 8
    readonly property int espacoLinha: 14
    readonly property int margem: 16

    readonly property int fonte: 15
    readonly property int fonteSecundaria: 14
    readonly property int fonteTitulo: 17

    // Abaixo disto, rótulo e controle deixam de caber lado a lado e passam a empilhar.
    // É o conceito que o QLayout não tem: ponto de quebra.
    readonly property int larguraDeQuebra: 520
}
