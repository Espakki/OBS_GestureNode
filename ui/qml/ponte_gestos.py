"""A aba Gestos exposta ao QML. Ver D-49.

A diferença de desenho em relação à aba Geral: aqui os campos escrevem **direto** no
binding do gesto selecionado, em vez de emitir pedido. Cena, som e atalho só guardam valor,
e o `EstadoApp.definir_binding` já cuida de notificar e de não gravar o que não mudou.

O que continua emitindo pedido é o que tem consequência fora do estado: escolher os gestos
ativos abre um diálogo, procurar som abre o seletor de arquivo do sistema, e reconfigurar a
engine em execução é decisão da janela.

**A captura de atalho não reimplementa nada.** Ela recolhe os números do evento e chama
`ui/atalho_capturado.py` — a mesma função que o `HotkeyLineEdit` de Widgets usa. É o que
garante que a proteção contra AltGr (D-50) valha nas duas telas.
"""

import os

from PySide6.QtCore import Property, QObject, Signal, Slot

from ui import atalho_capturado
from util.logger import get_logger

logger = get_logger(__name__)

HOLD_MINIMO, HOLD_MAXIMO = 0.5, 5.0
COOLDOWN_MINIMO, COOLDOWN_MAXIMO = 2.0, 20.0


class PonteGestos(QObject):

    mudou = Signal()
    gestosMudaram = Signal()
    capturaMudou = Signal()

    gestoTrocado = Signal(str)
    escolherGestosPedido = Signal()
    procurarSomPedido = Signal()
    bindingEditado = Signal()

    # A interface nova liga e desliga o gesto no próprio cartão, em vez de abrir o diálogo
    # modal. O sinal existe porque quem valida ("é preciso ao menos um gesto ativo") e quem
    # sincroniza a engine é a janela, não a ponte.
    ativoAlternado = Signal(str, bool)
    todosMudaram = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)
        self._estado = estado
        self._gestos = []           # [(nome, url_do_icone)] — só os ativos, grade antiga
        self._todos = []            # [(nome, url_do_icone)] — os doze, grade nova
        self._atual = ""
        self._capturando = False
        self._segurados = set()
        self._parcial = ""

        self._cancelar = estado.escutar(self._ao_mudar_estado)

    def _ao_mudar_estado(self, campo, valor):
        self.mudou.emit()
        # O cartão da grade nova mostra o resumo da ação e o estado de ativo, então ele
        # também precisa redesenhar quando o binding muda — não só quando a lista muda.
        self.todosMudaram.emit()

    def desligar(self):
        """Cancela a inscrição no estado.

        Sem isto, uma ponte destruída continua na lista de ouvintes do `EstadoApp` e
        estoura `Internal C++ object already deleted` a **cada** mudança de estado, para
        sempre. O `EstadoApp` engole a exceção (por desenho: um ouvinte quebrado não pode
        derrubar quem mexeu num slider), então o vazamento não aparece como falha — aparece
        como um traceback no log a cada clique.
        """
        if self._cancelar is not None:
            self._cancelar()
            self._cancelar = None

    # ------------------------------------------------------------------ grade

    @Property(list, notify=gestosMudaram)
    def gestos(self):
        return [{"nome": nome, "icone": icone} for nome, icone in self._gestos]

    @Property(str, notify=gestosMudaram)
    def gestoAtual(self):
        return self._atual

    def definir_gestos(self, entradas, selecionado):
        self._gestos = list(entradas)
        self._atual = selecionado or (self._gestos[0][0] if self._gestos else "")
        self.gestosMudaram.emit()

    # --------------------------------------------------- grade da interface nova
    #
    # A grade antiga recebe só os gestos ATIVOS, porque ativar era papel do diálogo. A
    # nova mostra os doze e traz o estado junto, para o interruptor morar no cartão.

    @Property(list, notify=todosMudaram)
    def todosOsGestos(self):
        ativos = set(self._estado.gestos_ativos)
        saida = []
        for nome, icone in self._todos:
            saida.append({
                "nome": nome,
                "icone": icone,
                "ativo": nome in ativos,
                "resumo": self._resumo(nome) if nome in ativos else "",
            })
        return saida

    def definir_todos(self, entradas):
        self._todos = list(entradas)
        self.todosMudaram.emit()

    def _resumo(self, nome):
        """O que este gesto faz, em uma linha — para o cartão dizer sem precisar do clique."""
        b = self._estado.binding(nome)
        partes = []
        if b.get("use_scene") and b.get("scene"):
            partes.append("Cena: " + str(b["scene"]))
        if b.get("use_hotkey") and b.get("hotkey"):
            partes.append(str(b["hotkey"]))
        if b.get("use_sound") and b.get("sound_file"):
            partes.append("Som")
        return " · ".join(partes)

    @Slot(str, bool)
    def alternarAtivo(self, nome, ligado):
        self.ativoAlternado.emit(str(nome), bool(ligado))

    @Slot(str)
    def selecionarGesto(self, nome):
        # Só gesto que está na grade: aceitar um gesto inativo deixaria o cabeçalho
        # dizendo "Configurando: X" com X sem cartão nenhum na tela.
        if nome not in {n for n, _ in self._gestos}:
            return

        if nome and nome != self._atual:
            self._atual = nome
            self._cancelar_captura()
            self.gestosMudaram.emit()
            self.mudou.emit()
            self.gestoTrocado.emit(nome)

    @Slot()
    def escolherGestos(self):
        self.escolherGestosPedido.emit()

    # ------------------------------------------------------------------ binding

    def _binding(self):
        if not self._atual:
            return {}
        return self._estado.binding(self._atual)

    def _gravar(self, **campos):
        if not self._atual:
            return
        self._estado.definir_binding(self._atual, **campos)
        self.mudou.emit()
        self.bindingEditado.emit()

    @Property(float, notify=mudou)
    def holdTime(self):
        return float(self._binding().get("hold_time", HOLD_MINIMO))

    @Property(float, notify=mudou)
    def cooldown(self):
        return float(self._binding().get("cooldown", COOLDOWN_MINIMO))

    @Property(bool, notify=mudou)
    def usaCena(self):
        return bool(self._binding().get("use_scene", False))

    @Property(bool, notify=mudou)
    def usaSom(self):
        return bool(self._binding().get("use_sound", False))

    @Property(bool, notify=mudou)
    def usaAtalho(self):
        return bool(self._binding().get("use_hotkey", False))

    @Property(str, notify=mudou)
    def cena(self):
        return self._binding().get("scene", "")

    @Property(str, notify=mudou)
    def arquivoDeSom(self):
        return self._binding().get("sound_file", "")

    @Property(str, notify=mudou)
    def atalho(self):
        return self._binding().get("hotkey", "")

    @Property(str, notify=mudou)
    def erroDoSom(self):
        """Aviso de arquivo ausente, calculado na hora de mostrar.

        Não é erro de validação: o arquivo pode estar num drive que ainda vai ser montado.
        Some sozinho quando o caminho volta a existir.
        """
        caminho = self.arquivoDeSom.strip()
        if caminho and not os.path.isfile(caminho):
            return f"Arquivo não encontrado: {caminho}"
        return ""

    @Slot(float)
    def definirHold(self, valor):
        self._gravar(hold_time=max(HOLD_MINIMO, min(HOLD_MAXIMO, float(valor))))

    @Slot(float)
    def definirCooldown(self, valor):
        self._gravar(cooldown=max(COOLDOWN_MINIMO, min(COOLDOWN_MAXIMO, float(valor))))

    @Slot(bool)
    def alternarCena(self, ligado):
        self._gravar(use_scene=bool(ligado))

    @Slot(bool)
    def alternarSom(self, ligado):
        # `play_sound` é o campo que a engine lê; `use_sound` é o que a tela marca. Manter
        # os dois juntos evita o estado em que a caixa está marcada e nada toca.
        self._gravar(use_sound=bool(ligado), play_sound=bool(ligado))

    @Slot(bool)
    def alternarAtalho(self, ligado):
        self._gravar(use_hotkey=bool(ligado))

    @Slot(str)
    def definirCena(self, texto):
        self._gravar(scene=texto.strip())

    @Slot(str)
    def definirArquivoDeSom(self, caminho):
        self._gravar(sound_file=caminho.strip())

    @Slot()
    def procurarSom(self):
        self.procurarSomPedido.emit()

    # ------------------------------------------------------------------ captura

    @Property(bool, notify=capturaMudou)
    def capturando(self):
        return self._capturando

    @Property(str, notify=capturaMudou)
    def atalhoParcial(self):
        """"Ctrl+Shift+..." enquanto o usuário só segura os modificadores."""
        return self._parcial

    @Slot()
    def iniciarCaptura(self):
        self._capturando = True
        self._segurados = set()
        self._parcial = ""
        self.capturaMudou.emit()

    @Slot()
    def cancelarCaptura(self):
        self._cancelar_captura()

    def _cancelar_captura(self):
        if not self._capturando:
            return
        self._capturando = False
        self._segurados = set()
        self._parcial = ""
        self.capturaMudou.emit()

    @Slot(int, int, str, int, result=bool)
    def teclaPressionada(self, codigo, flags, texto, vk_nativo):
        """Devolve `True` quando a combinação foi fechada e gravada.

        Toda a tradução — inclusive a defesa contra AltGr — vem de
        `ui/atalho_capturado.py`, a mesma função da versão em Widgets. Ver D-50.
        """
        if not self._capturando:
            return False

        if atalho_capturado.e_modificador(codigo):
            self._segurados.add(codigo)
            mods = atalho_capturado.modificadores_de_teclas(self._segurados)
            self._parcial = "+".join(mods) + "+..." if mods else ""
            self.capturaMudou.emit()
            return False

        combinacao = atalho_capturado.montar(
            codigo, flags, texto, vk_nativo, segurados=self._segurados
        )
        if not combinacao:
            return False

        self._capturando = False
        self._segurados = set()
        self._parcial = ""
        self.capturaMudou.emit()
        self._gravar(hotkey=combinacao)
        return True

    @Slot(int)
    def teclaSolta(self, codigo):
        if self._capturando and codigo in self._segurados:
            self._segurados.discard(codigo)
            mods = atalho_capturado.modificadores_de_teclas(self._segurados)
            self._parcial = "+".join(mods) + "+..." if mods else ""
            self.capturaMudou.emit()

    @Slot()
    def limparAtalho(self):
        self._gravar(hotkey="")
