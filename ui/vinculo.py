"""A guarda "isto é carga, não clique" — em um lugar só. Ver D-47.

O `setChecked`/`setValue` do Qt emite o mesmo sinal quer o usuário tenha clicado, quer o
código esteja refletindo o estado na tela. Como o handler não distingue os dois, **carregar
a config virava uma sequência de ações de usuário**: reescrevia a config, agendava save e
refazia o probe da câmera (D-41).

A resposta do projeto tinha sido espalhar guardas: `blockSignals` aos pares e flags como
`_updating_gesture_form`, contadas em 43 ocorrências. Cada campo novo pedia mais uma, e
esquecer não dava erro — dava um bug silencioso.

**Escopo deliberadamente pequeno.** Isto não é um sistema de binding declarativo, e não
deve virar um: reimplementar binding sobre Qt Widgets é escrever um mini-framework que o
Qt Quick já traz pronto. O que está aqui cobre os dois padrões que de fato se repetiam no
código, e para.
"""

from contextlib import contextmanager


@contextmanager
def sem_sinais(*widgets):
    """Altera widgets sem que a alteração pareça um clique do usuário.

    Restaura no `finally`: uma exceção no meio da carga não pode deixar a interface muda
    para sempre — o usuário mexeria nos controles e nada responderia.
    """
    anteriores = [(w, w.blockSignals(True)) for w in widgets]
    try:
        yield
    finally:
        for widget, anterior in anteriores:
            widget.blockSignals(anterior)


def espelhar(slider, spin, fator=10.0):
    """Mantém um slider inteiro e um spin decimal mostrando o mesmo número.

    O slider trabalha em décimos (`fator=10`) porque `QSlider` só é inteiro. Cada lado
    escreve no outro com os sinais bloqueados, senão a escrita volta e os dois ficam se
    empurrando.

    Substitui quatro handlers quase idênticos — `on_hold_slider_changed`,
    `on_hold_spinbox_changed`, `on_cooldown_slider_changed`, `on_cooldown_spinbox_changed` —
    que existiam só para fazer isto, cada um com seu par de `blockSignals`.
    """

    def do_slider(valor):
        with sem_sinais(spin):
            spin.setValue(valor / fator)

    def do_spin(valor):
        with sem_sinais(slider):
            slider.setValue(int(round(valor * fator)))

    slider.valueChanged.connect(do_slider)
    spin.valueChanged.connect(do_spin)


def refletir(widgets, aplicar):
    """Executa `aplicar()` com `widgets` mudos. Para os `set_*` que refletem estado."""
    with sem_sinais(*widgets):
        aplicar()
