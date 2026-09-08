"""O contrato que as duas implementações da aba Geral cumprem. Ver D-49.

Enquanto existia uma implementação só, os mixins alcançavam os widgets dela direto —
`self.camera_device_combo.currentText()`, `self.resolution_buttons[rotulo].setEnabled(...)`,
`self.health_camera.setStyleSheet(...)`. Isso amarrava a lógica da janela ao **jeito** de a
aba ser desenhada, e é por isso que trocar de framework parecia caro: não era a tela que
prendia, era o alcance dela.

Com este contrato, quem chama passa a dizer *o que* quer — "estas resoluções não estão
disponíveis", "a saúde é esta" — e cada aba resolve como mostrar. A de Widgets desabilita
botões e escreve QSS inline; a de QML publica na ponte e deixa a ligação redesenhar.

**Isto não é abstração especulativa.** Existem duas implementações agora, e a segunda só é
possível por causa dele.

O contrato tem dois lados:

- **Sinais**, o que o usuário pediu. Nomeados por intenção (`resolucaoPedida`), não por
  widget (`resolution_button_toggled`): quem escuta não deve saber se aquilo veio de um
  botão, de um menu ou de um atalho.
- **Métodos**, o que a janela quer refletir na tela.

Nenhum dos dois expõe widget. É a regra inteira.
"""

# --- Sinais que a aba emite -------------------------------------------------------------
#
#   modoPedido(str)          "teste" | "manual" | "automatico"
#   maosPedidas(int)         1 ou 2
#   resolucaoPedida(str)     rótulo de RESOLUTION_PRESETS: "480p", "720p", "1080p"
#   fpsPedido(int)           30 ou 60
#   cameraPedida(int)        índice do DISPOSITIVO, não a posição na lista
#   esqueletoPedido()        algum dos dois toggles de esqueleto mudou
#   recomendadoPedido()      clicou em "usar configuração recomendada"
#
# --- Métodos que a aba oferece ----------------------------------------------------------
#
#   set_mode(modo)                          reflete o modo
#   set_max_maos(n)
#   set_resolution(rotulo)
#   set_fps(valor)
#   set_esqueleto(no_preview, na_saida_obs)
#
#   definir_cameras(entradas, indice_do_dispositivo)
#       `entradas` é uma lista de `(nome_exibido, indice_do_dispositivo)`.
#       A distinção importa: a lista é reordenada (câmera virtual vai para o fim), então
#       posição na lista e índice do dispositivo divergem — e confundir os dois abre a
#       câmera errada.
#
#   camera_atual() -> (nome, indice_do_dispositivo)
#
#   definir_capacidades(resolucoes_off, fps_off, aviso, tem_recomendacao)
#       O que a câmera NÃO oferece, mais o texto da faixa. Quem decide o texto é o
#       chamador, porque a regra é de domínio (D-45); a aba só o mostra.
#
#   definir_saude(linhas)
#       Sequência de `(titulo, severidade, detalhe)`. Severidade é uma das de SEVERIDADES.
#
#   definir_controles_habilitados(ligado)
#       Trava o que não pode mudar com a engine rodando.
#
#   update_latency_badge(ms) / reset_latency_badge()

SEVERIDADES = ("ok", "warn", "error", "idle")

SINAIS = (
    "modoPedido",
    "maosPedidas",
    "resolucaoPedida",
    "fpsPedido",
    "cameraPedida",
    "esqueletoPedido",
    "recomendadoPedido",
)

METODOS = (
    "set_mode",
    "set_max_maos",
    "set_resolution",
    "set_fps",
    "set_esqueleto",
    "definir_cameras",
    "camera_atual",
    "definir_capacidades",
    "definir_saude",
    "definir_controles_habilitados",
    "update_latency_badge",
    "reset_latency_badge",
)
