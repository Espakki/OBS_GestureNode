pragma Singleton
import QtQuick
import novo

// Tokens da remodelagem. Herda a identidade roxa do tema atual, corrige os cinco casos de
// contraste que reprovaram no WCAG AA e acrescenta o que faltava: elevação (o tema de hoje
// tem 3 superfícies e usa borda para tudo) e uma escala tipográfica de verdade.
QtObject {
    // --- superfícies: 5 níveis, do fundo para a frente ---
    readonly property color fundo:      "#0b0b0f"
    readonly property color superficie: "#131319"
    readonly property color elevada:    "#1a1a22"
    readonly property color controle:   "#22222c"
    readonly property color controleHover: "#2b2b37"
    readonly property color controlePressionado: "#1c1c25"
    readonly property color controleDesabilitado: "#16161d"

    // --- traços: subidos para passar de 3:1 contra o fundo ---
    readonly property color borda:      "#60607a"   // 3.23:1 contra o fundo — WCAG 1.4.11
    readonly property color bordaHover:  "#7a7a99"
    readonly property color bordaSutil:  "#26262f"
    readonly property color bordaDesabilitada: "#1e1e26"

    // --- texto: os dois tons apagados subiram; era onde estava a reprovação ---
    readonly property color texto:            "#f2f2f6"
    readonly property color textoSecundario:  "#b4b4c4"
    readonly property color textoApagado:     "#8e8ea3"
    readonly property color textoDesabilitado:"#6e6e8a"  // 3.20:1 contra o controle
    readonly property color textoSobreDestaque: "#ffffff"

    // --- destaque ---
    readonly property color destaque:           "#7c5cff"
    readonly property color destaqueHover:      "#9a7dff"
    readonly property color destaquePressionado:"#6844e0"
    readonly property color destaqueFraco:      "#1e1733"
    readonly property color tituloSecao:        "#c9baff"

    // --- severidade ---
    readonly property color ok:      "#34d399"
    readonly property color atencao: "#fbbf24"
    readonly property color erro:    "#f87171"
    readonly property color neutro:  "#8e8ea3"
    readonly property color okFraco:      "#0f2a22"
    readonly property color atencaoFraco: "#2a2010"
    readonly property color erroFraco:    "#2a1414"

    // --- métrica ---
    readonly property int raio: 10
    readonly property int raioPequeno: 7
    readonly property int raioGrande: 14
    readonly property int alturaControle: 40
    readonly property int alturaBarra: 60
    readonly property int larguraRail: 208
    readonly property int larguraPainel: 372

    readonly property int e1: 4
    readonly property int e2: 8
    readonly property int e3: 12
    readonly property int e4: 16
    readonly property int e5: 24
    readonly property int e6: 32

    // --- tipografia: escala nomeada, em vez de 3 tamanhos avulsos ---
    readonly property string familia: "Segoe UI"
    readonly property int fonteMicro: 11
    readonly property int fonteMiuda: 12
    readonly property int fonteCorpo: 14
    readonly property int fonteCorpoG: 15
    readonly property int fonteTitulo: 18
    readonly property int fonteDisplay: 24
}
