"""O onboarding, com o texto conferido contra a interface que existe. Ver D-52.

**Por que o conteúdo mudou junto com a tecnologia.** O onboarding de Widgets mandava o
usuário clicar em coisas que não existem mais: "Selecionar gestos ativos" (o botão dizia
"Escolher gestos"), "Tempo de resposta" (o campo diz "Segurar por") e "o modo da câmera
virtual" dentro de Configurações Avançadas — painel que só tinha resolução e FPS. Pior, o
passo 1 chamava Automático/Manual de modo da câmera virtual e o passo 2 chamava os mesmos
nomes de modo de operação, contradizendo a si mesmo em duas telas de distância.

Um onboarding que ensina errado é pior que nenhum: ele gasta a confiança do usuário logo no
primeiro minuto. Cada passo aqui foi escrito olhando a tela correspondente da interface
nova, e a numeração dos passos acompanha a ordem do rail.

Segue a assimetria das outras pontes: estado → tela por `@Property` com `notify`, tela →
Python por `@Slot`.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from util.logger import get_logger

logger = get_logger(__name__)


PASSOS = [
    {
        "titulo": "Escolha a câmera",
        "glifo": "◎",
        "corpo": "Abra <b>Câmera</b> no menu à esquerda e selecione o seu dispositivo.\n\n"
                 "Logo abaixo ficam a resolução e a taxa de quadros. Opções que a sua "
                 "câmera não aceita aparecem apagadas, e o app sugere a combinação que "
                 "ela suporta.\n\n"
                 "A imagem é usada só para detectar gestos — nada é gravado nem enviado "
                 "para servidor nenhum.",
    },
    {
        "titulo": "Escolha o modo",
        "glifo": "⚡",
        "corpo": "Ainda em <b>Câmera</b>, no topo, ficam os três modos de operação:\n\n"
                 "<b>Teste</b> — detecta e mostra os gestos, mas não executa nada. É por "
                 "onde começar.\n\n"
                 "<b>Manual</b> — conecta ao OBS e executa as ações, com a câmera virtual "
                 "desligada.\n\n"
                 "<b>Automático</b> — como o Manual, e ainda liga a câmera virtual ao "
                 "iniciar. É o modo do uso normal.",
    },
    {
        "titulo": "Conecte o OBS",
        "glifo": "▣",
        "corpo": "Necessário nos modos Manual e Automático.\n\n"
                 "No OBS, abra <b>Ferramentas → Configurações do servidor WebSocket</b> e "
                 "ative o servidor. Copie a senha, se houver.\n\n"
                 "Depois abra <b>OBS</b> no menu à esquerda, preencha host, porta e senha, "
                 "e clique em <b>Testar conexão</b>.",
    },
    {
        "titulo": "Configure um gesto",
        "glifo": "✋",
        "corpo": "Em <b>Gestos</b>, cada cartão tem um interruptor no canto: ligue o gesto "
                 "que quiser usar.\n\n"
                 "Clique no cartão para configurar a ação no painel à direita — trocar "
                 "cena, tocar um som ou enviar um atalho de teclado.\n\n"
                 "<b>Segurar por</b> é quanto tempo a mão precisa ficar parada para "
                 "disparar. O app diz, embaixo do controle, se o valor escolhido é seguro "
                 "para uso ao vivo.\n\n"
                 "Depois é só clicar em <b>Iniciar</b>, no alto à direita.",
    },
]


class PonteOnboarding(QObject):
    """Os quatro passos de boas-vindas, como sobreposição da própria janela."""

    mudou = Signal()
    concluido = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)
        self._estado = estado
        self._passo = 0
        self._visivel = False

    # ------------------------------------------------------------------ estado

    @Property(bool, notify=mudou)
    def visivel(self):
        return self._visivel

    @Property(int, notify=mudou)
    def passo(self):
        return self._passo

    @Property(int, notify=mudou)
    def total(self):
        return len(PASSOS)

    @Property(str, notify=mudou)
    def titulo(self):
        return PASSOS[self._passo]["titulo"]

    @Property(str, notify=mudou)
    def glifo(self):
        return PASSOS[self._passo]["glifo"]

    @Property(str, notify=mudou)
    def corpo(self):
        # `\n\n` vira parágrafo; o QML desenha com StyledText, que aceita <b> e <br>.
        return PASSOS[self._passo]["corpo"].replace("\n\n", "<br><br>")

    @Property(bool, notify=mudou)
    def temAnterior(self):
        return self._passo > 0

    @Property(bool, notify=mudou)
    def ehUltimo(self):
        return self._passo == len(PASSOS) - 1

    def abrir(self):
        self._passo = 0
        self._visivel = True
        self.mudou.emit()

    # ------------------------------------------------------------------- ações

    @Slot()
    def avancar(self):
        if self._passo < len(PASSOS) - 1:
            self._passo += 1
            self.mudou.emit()
        else:
            self._concluir()

    @Slot()
    def voltar(self):
        if self._passo > 0:
            self._passo -= 1
            self.mudou.emit()

    @Slot(int)
    def irPara(self, indice):
        if 0 <= indice < len(PASSOS):
            self._passo = int(indice)
            self.mudou.emit()

    @Slot()
    def pular(self):
        """Sair sem ler também marca como feito.

        Quem pula não quer ver de novo no próximo boot — repetir seria punir a escolha.
        """
        self._concluir()

    def _concluir(self):
        self._visivel = False
        # O estado cuida de notificar e salvar, como qualquer outra mudança. Ver D-47.
        self._estado.onboarding_feito = True
        self.mudou.emit()
        self.concluido.emit()
