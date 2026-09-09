# Decisões

Log append-only. Nunca reescreva nem apague uma entrada — se uma decisão muda, adicione uma
nova que a substitui e marque a antiga como **substituída por**.

**Leia antes de julgar código como estranho.** Várias escolhas aqui parecem inconsistência
até você conhecer o motivo. Se você está prestes a "consertar" algo que está nesta lista,
o que você quer é uma nova decisão, não um patch.

`FIXA` = invariante. Não mexa sem uma decisão nova que justifique.

---

## Detecção e engine

**D-01 · `FIXA` · Handedness é invertido na saída do HandTracker**
*Origem: fase 9 · 2026-06-27*
MediaPipe retorna handedness invertido para frames pré-espelhados (câmera frontal): label
`"Right"` no resultado = mão física **esquerda** do usuário. A inversão é aplicada dentro de
`HandTracker.processar()`, então a engine recebe o label fisicamente correto e não tem
lógica de inversão própria.
**Por quê:** um único ponto de inversão. Espalhar isso pela engine garante que alguém
inverta duas vezes.

**D-02 · Cooldown é compartilhado por gesto entre as mãos, não per-hand**
*Origem: fase 9 (D-05) · 2026-06-27*
`ultimo_disparo_por_gesto` é um dict único chaveado só pelo nome do gesto. Se "Joinha"
disparou em qualquer mão, **ambas** ficam bloqueadas pelo cooldown — primeira mão vence.
**Por quê:** evita duplo-disparo acidental quando as duas mãos fazem o mesmo gesto.
**Nota:** todo o resto do estado (`detection_window`, `stability_monitor`, `gesto_ativo`,
`inicio_gesto`) **é** per-hand. A assimetria é intencional, não um descuido — já foi
reportada como bug uma vez, por leitura do código sem esta decisão.

**D-31 · Gestos combinados descartados; duas mãos servem para "a primeira vence"**
*2026-09-04* · **substitui D-30**

Gestos combinados foram **removidos**. A ideia vinha do planning antigo, chegou a ser
implementada (D-30) e foi descartada pelo dono do projeto na revisão.

**Por quê:** o usuário-alvo é streamer com as mãos ocupadas — controle, teclado, mouse.
Exigir que ele solte tudo e posicione as **duas** mãos na câmera para trocar de cena
contraria o motivo do app existir. Uma mão é o necessário.

**O que as duas mãos passam a resolver.** `max_maos=2` continua, mas com outro propósito:
tolerância. Antes, ter a segunda mão em quadro criava o problema de "qual mão é a certa".
Agora as duas são rastreadas, e **a primeira a fazer o gesto vence** — o usuário não
precisa esconder uma mão nem lembrar qual é a válida.

**Regra de despacho:** no máximo uma ação por vez, da mão com o menor `inicio` de gesto (a
que está segurando há mais tempo). Determinístico e independente da ordem em que o
MediaPipe devolveu as mãos.
**Substitui o D-03**, que mandava cada mão disparar sua própria binding
independentemente: duas mãos com gestos diferentes trocariam duas cenas de uma vez.

**Detalhe deliberado:** se a mão que chegou primeiro ainda não está estável, **nada
dispara** — ela não passa a vez. Sem isso, tremer a mão da frente faria a ação da *outra*
mão disparar, o que é surpreendente. Fixado em
`tests/test_despacho_por_mao.py::test_vencedora_instavel_nao_passa_a_vez`.

**O que sobreviveu do B-07:** a reestruturação do `run()` em duas passadas (colher o estado
de cada mão, depois despachar) e o `_tentar_disparar()` extraído. Foram feitos para o
combinado, mas são exatamente o que a regra "primeira vence" precisa — sem eles não há como
comparar as mãos antes de agir.

`combined_bindings` é removido do config na carga, como o `virtual_cam_mode` do D-11.

**D-30 · ~~Gestos combinados: par não ordenado que suprime os individuais~~ REVERTIDO**
*2026-09-04 · B-07* · **substituída por D-31**

Fecha a última feature que o planning antigo deixou aberta. O campo `combined_bindings`
existia no config desde a fase 9, mas nenhum código o consumia.

**Par não ordenado.** A chave canônica é `"Joinha + V"` — os dois nomes ordenados
alfabeticamente, montada por `core/gestos_combinados.py`.
**Por quê:** o D-03 já definiu que a identidade da mão não importa para bindings
individuais (Joinha aciona a mesma ação vindo da esquerda ou da direita). Seria incoerente
o combinado passar a distinguir mãos quando o individual não distingue.

**O combinado suprime os individuais — e é a razão da feature funcionar.** Sem isso,
segurar V numa mão e Joinha na outra dispararia **três** ações: a de V, a de Joinha e a do
par, provavelmente trocando de cena três vezes.

A supressão vale **desde que o par é reconhecido**, não só depois que o combinado completa
o hold. Se esperasse, o individual (que tem hold próprio, normalmente menor) ganharia a
corrida sempre e a supressão nunca teria efeito. Consequência aceita: formar um par e
desfazer antes do hold não dispara nada. É previsível — "enquanto você está formando um
combo, os individuais não disparam".

**Hold contado a partir da formação do par**, não do início do gesto de cada mão. As mãos
raramente fecham o gesto no mesmo frame; usar o início de uma delas daria vantagem
arbitrária à que chegou primeiro. O par também precisa das **duas** mãos estáveis.

**Reestruturação do loop.** `run()` despachava dentro do `for mao in maos`, o que tornava a
supressão impossível — quando a segunda mão era avaliada, a primeira já tinha disparado.
Agora são duas passadas: colher o gesto estável de cada mão, decidir se há combinado,
depois despachar. O despacho virou `_tentar_disparar()`, compartilhado por individual e
combinado.

**UI: o par é só mais uma entrada no grid.** Um combinado aparece como botão `"Joinha + V"`
ao lado dos gestos normais, e o editor existente (hold, cooldown, cena, som, atalho) serve
sem alteração — os dois tipos de binding têm exatamente os mesmos campos. O que muda é só
de qual dict vem: `combined_bindings` em vez de `gestures.bindings`. Isso evitou uma
segunda tela de configuração inteira.

**Cooldown.** Combinado e individual convivem no mesmo registro de disparo. Não colidem
porque a chave do par contém `" + "`, que nenhum nome de gesto individual tem.

**D-03 · Cada mão dispara sua própria binding, independentemente**
*Origem: fase 9 (D-04) · 2026-06-27*
As duas mãos usam o mesmo pool de bindings. "Joinha" na esquerda **ou** na direita aciona a
mesma ação configurada. Sem bindings separadas por mão.
**Por quê:** zero migração de config e nenhuma UI nova. Bindings por mão, se um dia fizerem
sentido, são decisão futura.

**D-04 · `FIXA` · `model_complexity=0` no MediaPipe Hands**
*Origem: fase 9 (D-12) · 2026-06-27*
Obrigatório para sustentar 20–28 FPS em modo 2 mãos.
**Por quê:** o modelo lite foi medido em ~40–55% de ganho. Subir a complexidade derruba o
FPS abaixo do usável em 2 mãos.

**D-05 · `max_maos` no config, default 1**
*Origem: fase 9 (D-09) · 2026-06-27*
Lido com `.get("max_maos", 1)`. Sem migração: configs antigas carregam em modo 1 mão.

**D-06 · Trocar 1↔2 mãos com a engine rodando reinicia a engine**
*Origem: fase 9 (D-10, D-11) · 2026-06-27*
Engine parada: persiste no config e aplica no próximo Start. Sem restart desnecessário.

**D-28 · Joinha/deslike por ângulo com zona morta, não por coordenada Y**
*2026-09-03 · B-06*

**Medição primeiro.** Rotacionando os landmarks sintéticos de −180° a +180°, os gestos de
dedo (FIST, V, POINT, Arminha, OPEN_HAND, CALL_ME, THREE, FOUR, ROCK, Dedo do Meio)
sobrevivem à volta **completa**. Só o polegar quebrava.

**A hipótese do backlog estava errada.** Dizia que `_finger_extended` falha sob rotação por
medir distância até o pulso. Não falha: distância do pulso à ponta é medida **radial**,
invariante a rotação em torno do pulso. Ninguém tinha medido — a suposição sobreviveu por
parecer plausível.

**O problema real era pior e mais estreito.** Com a regra antiga
(`y4 < y3 and y4 < y5`), um joinha inclinado ~70° era classificado como **DESLIKE** — o
gesto oposto, com confiança, sem sinal de ambiguidade. Com os dois ligados a cenas
diferentes, inclinar a mão trocava para a cena errada no meio da live. A fronteira também
era assimétrica de nascença (UP sobrevivia −25°/+115°, DOWN −115°/+45°), porque era efeito
colateral da posição dos pontos 3 e 5, não uma decisão.

**Não dá para tornar invariante a rotação.** Joinha e deslike são a mesma forma de mão
girada 180°: no referencial da própria mão são idênticos. A orientação absoluta é
informação essencial aqui, não defeito. Tentar eliminá-la tornaria os dois indistinguíveis.

**Solução.** `_angulo_do_polegar()` mede o ângulo do vetor ponto 2 → ponto 4 contra a
vertical da imagem. UP quando ≤ `TOLERANCIA_POLEGAR_GRAUS`, DOWN quando ≥ 180 − tolerância,
`None` no meio. Com 60°, a zona morta é 60°.
**A garantia que isso compra:** inverter joinha em deslike passa a ser **estruturalmente
impossível** sem atravessar a zona morta inteira. Não é medição empírica, é consequência da
forma da regra — e está fixada em
`tests/test_gesture_detector.py::TestRotacao::test_inverter_joinha_exige_atravessar_a_zona_morta`.

**Pendente de validação com câmera real:** o valor 60°. Maior = dispara com a mão mais
torta, mas encolhe a zona morta; menor = mais seguro, mas exige mão mais alinhada. Qual
inclinação as pessoas realmente usam ao fazer joinha é pergunta empírica, e chutar aqui
seria o mesmo erro do pin do `av` (D-24). A constante está isolada no topo de
`core/gesture_detector.py` para facilitar o ajuste.

**Efeito colateral:** poses de polegar muito horizontais que a regra antiga aceitava agora
caem na zona morta. É o comportamento desejado — ambíguo não deve disparar —, mas é
mudança observável.

**D-27 · `core/modos.py` é fonte única do modo; o check de velocidade foi renomeado**
*2026-09-03 · commit do B-04*

**Modo.** A migração de valor legado vivia duplicada em `ui/mixins/config_mixin.py` e
`engine/gesture_engine.py::_setup`. As duas cópias **já tinham divergido**: a da UI não
fazia `.lower()`, então `"TESTE"` virava `"automatico"` nela e `"teste"` na engine — a
interface mostrava Automático enquanto o motor rodava com todas as ações bloqueadas.
Mesma classe de bug do D-07 (três cópias de `GESTURE_ALIASES`), mesma solução: um módulo
pequeno, sem dependências, importado por quem precisar. A versão da engine venceu por ser
a mais tolerante. Agora aceita maiúsculas e espaço em volta.

**`_is_movement_decreasing` virou `_sem_aceleracao_brusca`.** O nome antigo prometia
exigir desaceleração, mas o método aceita movimento *crescente* desde que o crescimento
nos últimos 3 frames fique abaixo de `motion_threshold * 0.5` — com o default de 4px,
tolera crescer até 2px. É um filtro de arranco; quem faz o trabalho pesado de exigir mão
parada é o `stable_frame_count`.
**Por quê só renomear:** endurecer para exigir desaceleração de verdade mudaria *quando*
os gestos disparam, e isso precisa de validação com câmera real. É decisão de
comportamento, não limpeza — fica para o B-06. A semântica atual está fixada em
`tests/test_stability_monitor.py::TestSemAceleracaoBrusca`, então endurecer vai quebrar
teste de propósito.

**Também no mesmo passo:** `_hand_states` passa a ser acessado com `.get()` e ignora
handedness inesperado com log, em vez de estourar `KeyError` a cada frame dentro do loop
principal; `virtual_cam_mode` e `vcam_device` são removidos do config na carga, fechando
a pendência que o D-11 deixou aberta; e o import morto de `GESTURE_ALIASES` saiu do
`gesture_detector.py`.

**D-07 · `gesture_aliases.py` é fonte única de verdade dos nomes de gesto**
*Origem: fase 1 (D-07, D-09) · 2026-06-23*
Só o dict, sem helpers. Nasceu da união de 3 cópias divergidas que tinham valores
diferentes para os mesmos gestos (`ROCK` vs `Rock`), causando bindings que nunca casavam.
**Por quê:** qualquer módulo que precise do mapa importa deste arquivo. Nunca redeclare.

---

## Câmera e VCam

**D-46 · Linux não escolhe entre X11 e Wayland: tenta os injetores em ordem**
*2026-09-08 · B-23 · commit `f34fe59`*

O backlog do B-23 mandava **decidir antes**: X11, Wayland, ou os dois — anotando que
suportar os dois "quase dobra o trabalho da parte mais cara". Não escolhi nenhum dos dois,
e a razão é que a pergunta tinha uma premissa falsa.

**Nenhuma das duas opções cobre os usuários sozinha.** No X11, qualquer cliente pode falar
com o servidor e o `xdotool` resolve direto. No Wayland isso foi fechado por design, e
sobram dois caminhos incompatíveis entre si: o protocolo de teclado virtual, que o `wtype`
usa e que **GNOME e KDE não implementam**, ou o `uinput` do kernel, que o `ydotool` usa e
que funciona em qualquer sessão — ao custo de um daemon rodando e permissão no dispositivo.
Escolher só X11 deixaria de fora as distros mais recentes; escolher só Wayland via `wtype`
deixaria de fora justamente os dois desktops mais usados.

**A saída foi uma lista ordenada em vez de uma escolha.** `sessao_grafica()` lê o
`XDG_SESSION_TYPE`, com as variáveis de display como plano B, e `backends_preferidos()`
devolve a ordem: X11 → `xdotool`, `ydotool`; Wayland → `wtype`, `ydotool`; desconhecida →
os três. O `ydotool` é sempre o último porque é o que cobra algo do usuário.

**Um backend que falha não encerra a tentativa** — e isso não é robustez decorativa, é o
caso principal: no Wayland do GNOME o `wtype` está instalado e **sai com erro**, porque o
compositor não implementa o protocolo. Se a primeira falha abortasse, o GNOME nunca
chegaria no `ydotool`, que é o que funciona lá.

**Não dobrou o trabalho.** A previsão do backlog partia de "dois caminhos independentes",
mas os três backends compartilham só dois mapas de tecla: um de keysym do X11, que
`xdotool` e `wtype` usam igual, e um de código do kernel, que só o `ydotool` precisa. O
custo real foi o segundo mapa, não um port inteiro a mais.

**`_linux.py` importa em qualquer sistema, de propósito.** Ele não toca em API nativa — só
monta linha de comando e chama `subprocess`. Isso é o oposto do `_windows.py`, que só pode
ser importado no Windows, e é deliberado: deixa a lógica toda (detecção de sessão, ordem
dos backends, mapas de tecla, montagem do comando) coberta por teste automatizado rodando
**na única máquina que este projeto tem**, que é Windows. Foram 26 testes, validados por
mutação: 9 alterações no módulo, 9 pegas.

**O que os testes não provam, e precisa ficar claro:** que o comando montado funciona. A
forma da linha de comando está fixada; o efeito dela, não. Os mapas de keycode foram
escritos a partir do `input-event-codes.h` e nunca confrontados com um kernel. Enquanto
ninguém rodar em Linux real, o correto é dizer **"escrito, não verificado"** — o projeto já
levou essa lição uma vez com câmera e entrada de teclado.

**Paridade é testada, não torcida.** Um teste exige que toda tecla do `VK_NOMEADAS` do
Windows tenha keysym e keycode no Linux. O `config.json` é o mesmo arquivo nos dois
sistemas, então um atalho configurado no Windows atravessa para o Linux — sem a paridade,
ele viraria silêncio em vez de erro.

**Efeito colateral corrigido junto:** o `requirements.txt` instalava `pygrabber==0.2` sem
marcador. Ele fala DirectShow via `comtypes` e não existe fora do Windows, então
`pip install -r requirements.txt` quebrava no Linux antes de o app sequer subir. Agora é
`; sys_platform == "win32"`. Quem consome já tratava a ausência com fail-open (D-38), então
no Linux o app roda sem o filtro de capacidades da câmera — degrada, não quebra.

**Ainda fora do alcance desta decisão:** a câmera virtual. O `pyvirtualcam` no Linux exige o
módulo `v4l2loopback` carregado, o que é configuração de máquina e não de código. Sem ele,
o modo automático não tem para onde enviar o vídeo.

**D-45 · A faixa de limite da câmera é informação, e não pode falar como falha**
*2026-09-08 · B-25 · achado do dono na validação do `.exe`*

A faixa nasceu no D-39 âmbar, com borda e prefixo `⚠️`. O dono, ao usar o `.exe` pela
primeira vez, descreveu o efeito: **"dá sempre um sentimento de urgência sendo que não
tem"**. Ela é permanente — aparece sempre que a webcam não cobre algum preset — então esse
falso alarme fica na tela o tempo todo.

**O erro não era o âmbar em si, era o app se contradizer.** O `⚠️` não é um enfeite
genérico neste projeto: `ui/mixins/config_mixin.py` usa exatamente esse glifo para
"Não foi possível salvar as configurações", que é falha real e acionável. A faixa tomava
emprestado o vocabulário de falha para dizer um fato estático de hardware, que o usuário
não tem como mudar e sobre o qual não precisa fazer nada.

**O tooltip já denunciava o problema.** Ele terminava com "Não é erro do app" — uma faixa
que precisa desmentir a própria aparência está com a aparência errada. Removido o alarme,
a defesa deixou de ser necessária e saiu junto.

**O que mudou:** paleta neutra do tema (`#161616` de card, borda `#2d2d2d`, texto
`#a0a0a0`), sem glifo, e "Limite da sua câmera" → "Limites desta câmera". O corpo caiu para
14px, que é o tamanho de `muted` e `healthLabel` — a convenção do tema para texto
secundário. **Isso resolveu um segundo problema:** em 15px, com fundo e borda, a faixa
ficava quase idêntica ao botão "Usar configuração recomendada" logo abaixo, e podia ser
lida como um controle clicável. Menor, ela volta a ser texto.

**O D-39 continua de pé.** Ele decidiu que a limitação sai do log e vira faixa visível,
fora do painel avançado, porque no log some no scroll e o usuário fica encarando um botão
cinza. Nada disso mudou: a faixa continua visível, no mesmo lugar, dizendo a mesma coisa.
Mudou o tom. Um bloco distinto sobre o fundo `#0d0d0d` ainda se lê como bloco, sem gritar.

**Regra que fica:** `⚠️` e âmbar são reservados ao que o usuário pode e precisa resolver.
Limitação de hardware é informação — e informação usa a paleta neutra.

**D-43 · Script manual que testa lógica pura vira teste automatizado**
*2026-09-04*

`teste/` guardava dois scripts que não precisavam de hardware nenhum:
`test_hotkey_capture_logic.py` (eventos de tecla no `HotkeyLineEdit`, com Qt offscreen) e
`test_hotkey_dispatch.py` (normalização de texto de atalho — string pura).

Enquanto ficaram lá, **tiveram zero cobertura automática**: ninguém roda script manual
antes de commitar. Migrados para `tests/test_hotkeys.py`, viraram 19 testes que rodam em
0.3s junto com o resto.

**O que isso resgatou:** a regressão do **AltGr** (commit `8838edf`). Em layouts como o
ABNT2, Ctrl+Alt age como AltGr e o Qt entrega o caractere composto — `æ` no lugar de `z`.
Gravar isso produziria um atalho que nunca casa com o registrado no OBS. Validado por
mutação: fazer o campo preferir `event.text()` ao código da tecla quebra exatamente esse
teste.

**Critério para o que fica em `teste/`:** só o que exige webcam ou OBS ligado. O
`teste_pyav_vs_opencv.py` fica por valor histórico — foi a medição dele que motivou trocar
o OpenCV pelo PyAV na captura.

**D-42 · Tudo que depende do sistema operacional vive em `plataforma/`**
*2026-09-04 · B-22*

`actions/action_manager.py` fazia `import winsound` no topo. Como a cadeia
`main.py → ui → engine → action_manager` é toda import de nível de módulo, isso derrubava o
app em qualquer sistema que não fosse Windows **antes de a janela abrir**. Não era detalhe
de organização: era o bloqueador do port.

**O arquivo existir não é problema; o `import` executar é.** Distribuir `_windows.py` para
um usuário Linux custa alguns KB parados. Um `import winsound` no topo de um módulo sempre
carregado custa o app inteiro. A abstração existe para adiar o import até saber onde
estamos rodando.

**O nome é `plataforma`, não `platform`**, porque `platform` é módulo da stdlib — e o
próprio `action_manager` usava `platform.system()`. Um pacote com esse nome sombrearia a
stdlib inclusive para bibliotecas de terceiros.

```
plataforma/
  __init__.py    escolhe em runtime, olhando sys.platform
  _generico.py   teclado via pacote `keyboard`; base do futuro _linux.py
  _windows.py    winsound + SendInput — só importado no Windows
```

**Mover, não reescrever.** `action_manager.py` foi de 367 para 150 linhas e não sabe mais o
que é `ctypes` ou `winsound`; o que ficou é despacho e parsing, que não dependem de
sistema. Os 174 testes de então garantiram que o comportamento no Windows não mudou.

**Também atravessaram a fronteira:** o formato de captura (`dshow`/`v4l2`) e o
endereçamento do dispositivo — que não é só sintaxe, é identidade: o DirectShow endereça
por **nome**, o v4l2 por **número**. E o diretório de config, que passou a respeitar
`$XDG_CONFIG_HOME` fora do Windows.

**O teste que protege isso:** varre a árvore procurando `import` de API de sistema
(`winsound`, `msvcrt`, `fcntl`, `pwd`...) no topo de qualquer módulo fora de `plataforma/`.
Reintroduzir o padrão quebra na hora, em vez de aparecer quando alguém tentar rodar no
Linux.

**O que isto NÃO faz:** não implementa Linux (é o B-23) e não pode ser provado daqui.
Fingir `sys.platform` confunde bibliotecas de terceiros — o opencv passa a procurar API
POSIX. O que dá para provar, e foi provado, é que `action_manager` importa com `winsound`
inexistente.

**D-41 · Os `set_*` da aba Geral bloqueiam sinais: refletir config não é clicar**
*2026-09-04 · B-20*

O probe da câmera rodava duas vezes ao abrir o app. Rastreando a pilha, a causa era mais
larga que o desperdício de ~170ms:

```
_load_ui_from_config → set_resolution → toggled → on_resolution_changed → capacidades()
_load_ui_from_config → aplicar_capacidades_da_camera → capacidades()
```

`setChecked` emite `toggled`, e o handler não distingue "o usuário clicou" de "a config
está sendo carregada". Então **carregar a config disparava uma sequência de ações de
usuário**: reescrevia a config com os mesmos valores, agendava save e refazia o probe.

Os métodos `set_*` da aba existem para **refletir a config na interface** — o caminho
contrário. Agora todos passam por um `_sem_sinais()`, que bloqueia os botões durante a
marcação. Mesma ideia do `_updating_gesture_form` que a aba Gestos já usava.

**Corrigi a causa, não o sintoma.** Quando isso apareceu pela primeira vez — o aviso de
limitação saindo duplicado no log (D-38) — eu pus um guarda para não repetir a mensagem.
Isso escondeu o sinal sem tocar no que o produzia, e a duplicação continuou acontecendo
onde ninguém olhava.

**D-40 · A aba Geral fala por forma, não por parágrafo**
*2026-09-04*

Feedback do dono depois de ver a tela pronta: informação demais, texto demais — e isso com
o painel Configurações Avançadas ainda fechado. O princípio que ele deu vale como regra
para o resto da UI: **um bom UX conversa pelas formas, não pelas palavras.**

Redução medida nos trechos alterados: **440 → 126 caracteres (71%)**. O painel inteiro
ficou com 284 caracteres em 12 linhas.

| Trecho | Antes | Depois | O que mudou |
|---|---|---|---|
| Título "Configurações Gerais" | 20 | 0 | A aba já se chama Geral |
| Ajuda dos modos | 205 | 54 | Só o modo **selecionado**, uma linha |
| Checkbox do preview | 35 | 7 | Virou toggle "Preview" |
| Checkbox do OBS | 44 | 9 | Virou toggle "Saída OBS" |
| Faixa de limite | 136 | 56 | Só o fato; o resto foi para o tooltip |

**O esqueleto virou par de toggles**, no mesmo padrão visual de Modo e Mãos. É o ponto
central: a linha `Esqueleto: [Preview] [Saída OBS]` diz pela **forma** que são duas saídas
independentes — a mesma gramática visual que o usuário já aprendeu duas linhas acima. Dois
checkboxes com frases de 35 e 44 caracteres diziam o mesmo em prosa.

**Nada foi perdido, só movido.** Os tooltips já continham a explicação completa e
continuam lá — o texto visível estava **repetindo** o tooltip. A ajuda dos outros dois
modos não sumiu: ninguém precisa ler sobre um modo que não escolheu, e passar o mouse
mostra.

**D-39 · Limitação da câmera vira faixa na tela, e o preset recomendado depende do modo**
*2026-09-04 · B-12 + pedido de UI do dono*

**A limitação sai do log e vira faixa visível.** O D-38 já desabilitava o que a câmera não
tem, mas a explicação vivia no log e no tooltip — some no scroll, e o tooltip exige
adivinhar que é preciso passar o mouse. O usuário via um botão cinza sem saber por quê.

Agora há uma faixa na aba Geral, visível enquanto existir incompatibilidade:
*"Limitação da sua câmera: ela não faz 60 fps em 1920x1080 (máximo 30). As opções
indisponíveis ficam desabilitadas — não é erro do app."*

**Fica fora do painel Configurações Avançadas de propósito.** Os botões de resolução e FPS
moram lá dentro, e o painel nasce recolhido — um aviso ali só apareceria para quem já foi
procurar, que é exatamente quem não precisa dele.

**O aviso do log foi removido**, não somado. Manter os dois diria a mesma coisa em dois
lugares, e o pedido era justamente tirar do log.

**Botões continuam desabilitados**, em vez de clicáveis-que-recusam. Um botão que existe e
não funciona é pior que um botão apagado com explicação ao lado — e desabilitado torna
impossível salvar uma config quebrada.

---

**Preset recomendado (B-12): "melhor" depende do destino da imagem.**

- `teste` e `manual`: alvo **720p**. A captura só alimenta a inferência, que trabalha a
  `PROCESS_W = 640`. Acima de 720p custa CPU e não melhora detecção em nada.
- `automatico`: **maior resolução suportada**. A imagem vai para o OBS, então é o que o
  público vê.

O palpite óbvio — "pega sempre a maior suportada" — **estaria errado em dois dos três
modos**. Foi por isso que este item ficou separado do B-11: filtrar o que não existe é
objetivo, recomendar exige saber para onde a imagem vai.

O FPS escolhido é o maior que a resolução escolhida aceita, limitado ao que a UI oferece —
não adianta recomendar um modo que a câmera tem mas o app não expõe.

**Aplicado por botão, não automaticamente.** "Usar configuração recomendada" só aparece
quando há uma recomendação possível. Trocar a escolha do usuário sozinho, sem nada ter
falhado, seria mexer na config dele por antecipação — mesma razão do D-38.

**D-38 · Capacidades da câmera consultadas sob demanda, sem cache, com fail-open**
*2026-09-04 · B-11*

O app descobria o que a câmera não suporta **falhando** — e como o `[Errno 5]` do
DirectShow é o mesmo para "ocupado" e "modo inexistente" (D-32), a mensagem apontava para
o problema errado. Agora a UI pergunta antes.

**`pygrabber`, que já era dependência**, enumera os formatos sem abrir o dispositivo pelo
FFmpeg. Medido: ~130ms para listar dispositivos, ~44ms para enumerar formatos.

**Sem cache — e isso é o desenho, não preguiça.** O backlog previa guardar as capacidades
e invalidar por nome de dispositivo. Medido o custo, a consulta é barata o bastante para
rodar a cada troca de câmera ou resolução, o que **elimina a classe inteira de bug do cache
velho**: dado desatualizado esconderia modos que funcionam, e com a confiança de quem "já
analisou". Não guardar é mais simples e mais correto.

**Fail-open por princípio.** Se a consulta falhar, vier vazia, ou a câmera não reportar
modos MJPEG, `capacidades()` devolve `{}` e a UI **reabilita tudo**. Um probe quebrado não
pode trancar o usuário fora de opções que a câmera tem. O fallback de FPS do D-32 continua
sendo a rede embaixo — deixou de ser o mecanismo principal e virou a garantia final.

**A armadilha dos campos invertidos.** O pygrabber reporta `min_framerate=30,
max_framerate=5` para um modo cujo range real é 5–30 — provavelmente porque o DirectShow
expõe *intervalos entre frames*, e o menor intervalo é o maior FPS. Ler pelo nome do campo
inverteria toda a lógica e filtraria ao contrário. `_fps_maximo` pega o maior dos dois, o
que funciona nas duas convenções, e há teste fixando isso.

**Só modos MJPEG contam**, porque é o que `core/camera.py` pede. Um modo YUY2 a 60 fps não
ajuda em nada e daria uma falsa sensação de suporte.

**Não corrige a seleção do usuário sozinho.** A UI desabilita o que não existe e avisa no
log, mas não troca a escolha antes de nada ter falhado. Para o FPS, o D-32 ajusta na hora
de abrir e o D-34 devolve o valor real para a interface — o ciclo se fecha sem ninguém
mexer na config por antecipação.

**D-37 · Requisição recusada pelo OBS não derruba a conexão**
*2026-09-04 · B-15*

O usuário relatou que trocar o nome da cena de um gesto "não salvava" e só funcionava
depois de reiniciar a engine. **Não era sobre salvar.** Reproduzido: a config é gravada na
hora e a engine viva recebe o binding novo imediatamente. O problema estava depois.

`trocar_cena` capturava **qualquer** exceção e zerava `connected` e `cliente`. Como
`_connect_obs()` só roda na partida da engine, um único nome de cena inexistente matava o
OBS até reiniciar:

1. Nome de cena que o OBS não tem (digitando, ou erro de digitação)
2. O gesto dispara, `set_current_program_scene` levanta, **a conexão morre**
3. O usuário corrige o nome — e segue sem funcionar, porque já não há conexão
4. Reinicia a engine, reconecta, funciona

Daí a leitura de que "só salva reiniciando": o sintoma aparecia exatamente onde a config
estava certa.

**Solução:** `OBSSDKRequestError` significa que o OBS respondeu recusando — a conexão está
viva, então não se mexe nela. Qualquer outra exceção continua tratada como conexão perdida.

`trocar_cena` passa a devolver `(ok, mensagem)`, que sobe pelo `ActionManager` até o
`status_changed` da engine. Antes a falha morria no log: o gesto era reconhecido, o status
dizia que a cena mudou, e nada acontecia no OBS.

**Não fiz** validação prévia contra a lista de cenas do OBS. Seria mais elegante, mas
exige manter a lista sincronizada e trata como erro do usuário algo que pode ser só uma
cena criada depois. A mensagem específica no momento da falha resolve o caso real.

**D-36 · Tolerância do polegar baixada de 60° para 45°, calibrada com foto real**
*2026-09-04 · ajuste do D-28*

O D-28 escolheu 60° sem dado, e deixou registrado que o número precisava de validação com
mão real. Veio: foto de uma mão fechada com o polegar saindo na diagonal, a **~50° da
vertical**, sendo aceita como joinha. O usuário não considera aquilo um joinha — e é uma
pose fácil de fazer sem querer, com a mão relaxada ao lado do rosto.

**45°** rejeita aquela pose e alarga a zona morta de 60° para **90°**, o que também torna a
inversão joinha↔deslike ainda mais difícil.

**Por que o gate do D-35 não resolvia este caso, apesar de parecer o mesmo problema:** ali
o polegar aponta na *profundidade* e a projeção fica curta; aqui ele está no *plano da
imagem*, projeção longa, só que na diagonal. São dois eixos diferentes de erro e cada um
tem seu gate. O D-35 continua necessário — só não era esta a queixa.

**Trade-off aceito:** um joinha genuinamente inclinado além de 45° passa a não disparar. É
o lado seguro do erro para um app de live, onde um falso positivo troca de cena na frente
do público e um falso negativo só pede que o usuário repita o gesto.

`angulo_do_polegar()` virou público para permitir diagnóstico — dá para medir a pose real
antes de mexer no número de novo, em vez de calibrar no escuro.

**D-35 · O ângulo do polegar só vale se ele estiver de frente para a câmera**
*2026-09-04 · B-19 — polimento do D-28*

O D-28 resolveu a inclinação **no plano da imagem**. Ficou de fora a rotação em
**profundidade**: `_angulo_do_polegar` mede só X/Y, então um polegar apontando para a
câmera ou para longe dela projeta um vetor curto — cuja direção é quase ruído — e ainda
podia cair dentro dos 60° e virar joinha. Relatado como "joinha de lado, com o dedão
apontando para trás".

**Solução:** exigir que o polegar projetado tenha ao menos `COMPRIMENTO_MINIMO_POLEGAR`
(0.55) do `palm_size`. Medido nas mãos sintéticas: joinha e deslike de frente dão **0.83**,
um polegar em profundidade dá **0.44**. O corte rejeita o segundo com folga e aceita o
primeiro com muita. Em rotação de profundidade, equivale a exigir a mão a menos de ~48°
girada para o lado.

**Por que não usar o `z` do MediaPipe**, que seria o sinal direto: os landmarks hoje
trafegam como `(x, y)` em todo o detector e nos testes. Passar a `(x, y, z)` mudaria o
contrato de tudo, e o `z` do MediaPipe é relativo e notoriamente ruidoso. O comprimento
projetado resolve o caso real sem tocar no contrato — se um dia houver necessidade de
distinguir "para a câmera" de "para longe da câmera", aí o `z` se justifica.

**Invariante preservada:** o gate é distância, e distância não muda com rotação no plano.
Fixado em `TestPolegarEmProfundidade::test_o_gate_e_invariante_a_rotacao`, para que isto
não reintroduza a fragilidade que o D-28 removeu.

**Pendente de validação:** o valor 0.55, como o 60° do D-28. Se joinhas legítimos passarem
a ser recusados, é o primeiro número a baixar.

**D-34 · `stop()` é assíncrono; quem dirige a UI é o sinal `finished`**
*2026-09-04 · B-17, B-13*

**A parada não bloqueia mais (B-17).** `stop()` chamava `wait(8000)` a partir da thread da
UI, congelando a janela por ~2.5s (o `container.close()` do DirectShow, D-32) e fazendo o
app piscar. Agora `stop()` só sinaliza — medido, retorna em **0.1ms** contra ~2500ms.

Esperar era desnecessário: o Qt emite `finished` depois do `run()` retornar, ou seja depois
do `finally` já ter liberado câmera, OBS e executor. Quem precisa saber que a limpeza
acabou ouve o sinal. `esperar_ms` continua existindo para o `closeEvent`, único lugar onde
bloquear é correto — destruir uma QThread em execução derruba o processo.

**O bug que isso revelou.** `finished` era conectado **dentro do `stop_engine`**, ou seja,
só quando o usuário apertava Stop. Mas a engine também termina sozinha — falha ao abrir a
câmera é o caso comum — e aí o sinal disparava sem ninguém ouvindo: a UI ficava presa em
"rodando", com Start desabilitado. Pior depois que o `stop_engine` passou a desabilitar os
dois botões: apertar Stop nesse estado deixava **ambos travados para sempre**, porque o
`finished` que os reabilitaria já tinha passado. Agora a conexão é feita no `start_engine`,
uma vez por engine.

**FPS da UI acompanha o fallback (B-13).** Novo sinal `fps_ajustado`, emitido quando a
câmera recusa o FPS pedido (D-32). A UI corrige o botão e o config. Antes o usuário via o
aviso no status mas a interface seguia marcando 60 — discordando do que estava rodando.
`blockSignals` na correção evita disparar `on_fps_changed`, que gravaria de novo e poderia
pedir restart.

**D-33 · Traço do esqueleto proporcional; VCam em BGR; confirmação antes de reiniciar**
*2026-09-04 · B-14, B-16, B-18 — achados da primeira validação manual*

**Traço proporcional (B-14).** `draw_landmarks` usa `DrawingSpec(thickness=2)`, fixo em
pixels. Uma linha de 2px ocupa 0.31% da largura em 640px e 0.10% em 1920px. Na saída do
OBS isso foi percebido como "upscale da fonte" — **não era**: o frame nativo estava
correto desde o B-02, só o traço não acompanhava a escala. Agora a espessura deriva de
`PROCESS_W`, que é onde o valor 2 foi calibrado.

**VCam em `PixelFormat.BGR` (B-16).** O OpenCV já trabalha em BGR; a VCam era criada em RGB
e todo frame pagava um `cvtColor` de 2ms em 1080p só para desfazer isso.

**Cópia redundante removida (B-16).** O `frame_nativo.copy()` que o B-02 introduziu não
protegia nada: `ler_frame()` já devolve uma cópia privada e `processar()` não muta o frame
recebido. Custava 2.2ms por frame.

Somados, 3.8ms — 11% do orçamento de 33.3ms a 30 fps.

**O que NÃO era o problema, e por que fica registrado.** Com a VCam ligada o FPS caía de
28.7 para 20.5, e a hipótese natural era batimento entre pacers: `ler_frame` bloqueia
esperando frame novo, o loop tem cap de `process_fps`, e o `sleep_until_next_frame` da VCam
era um terceiro relógio. Removi o `sleep` — e o FPS **não melhorou** (19.2). Medindo os
componentes, o custo é do próprio `send()`: **9.3ms** para empurrar 6.2 MB de 1080p para a
memória compartilhada do OBS. A remoção foi revertida: não entregava nada e tirava a
proteção contra enviar mais rápido que o fps declarado.

**Teto realista deste caminho:** `processar` 23.2ms + `send` 9.3ms = 32.5ms contra um
intervalo de 33.3ms. Razor thin — qualquer jitter derruba um frame, daí os ~20 fps
observados em 1080p com VCam. Os dois custos dominantes (inferência do MediaPipe e o
`send` do OBS) são praticamente irredutíveis nesta arquitetura. Quem precisa de mais
fluidez e não depende de 1080p na saída ganha muito baixando a resolução de captura.

**`INTER_AREA` mantido.** Trocar por `INTER_LINEAR` economizaria 1.6ms, mas é a entrada da
inferência e `INTER_AREA` tem qualidade melhor em redução. Não troquei porque não dá para
medir o impacto na detecção sem mão real na frente da câmera — seria otimizar às cegas.

**Confirmação antes de reiniciar (B-18).** Trocar 1↔2 mãos com a engine rodando derruba e
religa a câmera. Acontecia sem aviso: a imagem sumia e voltava sozinha. Agora pergunta, e
reverte a seleção dos botões se o usuário recusar.

**D-32 · `[Errno 5]` do DirectShow é ambíguo: retry curto e depois fallback de FPS**
*2026-09-04*

O DirectShow devolve **o mesmo** `[Errno 5] I/O error` para dois problemas de naturezas
opostas, e o erro não distingue:

1. **Dispositivo ainda ocupado** — passa sozinho em ~1s. Insistir resolve.
2. **Modo não suportado** — não passa nunca. Insistir só gasta tempo.

Descoberto na prática: a C920 **não aceita 60 fps em resolução nenhuma** (testado em
1080p, 720p e 480p), e o `config.json` do usuário estava com `fps: 60`. O app falhava
sempre, com a mensagem "câmera ainda ocupada" — que mandava caçar o programa errado.
Nenhum programa estava segurando a câmera.

Pior: o retry introduzido para o caso 1 **agravou** o caso 2, insistindo 8 vezes numa
condição que jamais passaria, gastando ~5s antes de desistir.

**Solução:** retry curto (3 tentativas) para o caso 1, e então **uma tentativa com
`FPS_SEGURO = 30`** antes de desistir. Se essa abrir, o problema era o modo — o usuário
recebe "a câmera não aceita 60 fps nesta resolução, usando 30" em vez de uma pista falsa.
Se nem ela abrir, o erro original propaga: aí é ocupação de verdade.

**Ordem de abertura invertida:** o container passa a ser aberto **antes** da câmera
virtual. O fallback pode mudar o FPS efetivo, e criar a VCam antes a deixaria presa num
FPS que a captura não entrega. Como efeito colateral, reduz a superfície do vazamento de
VCam que o commit anterior corrigiu.

**Por que não remover 60 fps da UI:** câmeras melhores aceitam. Bloquear na interface
puniria quem tem hardware bom por causa de uma limitação da C920. O fallback com aviso
funciona para os dois casos.

**Pendência:** a UI não atualiza o botão de FPS quando o fallback acontece. O usuário vê o
aviso, mas o botão continua marcando 60 até ele trocar na mão.

**D-08 · Captura via PyAV/FFmpeg DirectShow, não OpenCV**
*Origem: fase 2 · commit `76607d8`*
Thread própria drenando o container, com `Condition` notificando por número de sequência.
`ler_frame()` bloqueia até um frame **novo** chegar.
**Por quê:** elimina frame staleness e o buffer interno do DirectShow, que entregava frames
atrasados. Ver [PITFALLS.md](PITFALLS.md).

**D-09 · ~~ABERTA~~ RESOLVIDA — o que a câmera virtual deve entregar?**
*2026-09-03* · **substituída por D-26**
A VCam recebia o frame de inferência (640px) upscalado de volta, não a captura nativa. A
pergunta era: frame nativo limpo, ou nativo com esqueleto?

**D-10 · Inicialização da VCam tem timeout de 3s em thread daemon**
*Origem: fase 13*
`pyvirtualcam.Camera()` trava indefinidamente quando o OBS segura o driver DirectShow com
exclusividade. Estourando o timeout, o app desliga a VCam e segue — o preview sempre sobe.
**Ordem correta de uso:** fechar OBS, iniciar o app, depois abrir OBS e adicionar a
"OBS Virtual Camera" como fonte.

**D-11 · Controles de VCam saíram da aba Geral**
*Origem: fase 15 (D-10, D-13)*
`vcam_mode_group`, `vcam_device_edit` e afins foram removidos. O campo `virtual_cam_mode` no
config deveria ter sido removido junto — ainda está lá. Ver B-04.

---

## OBS

**D-12 · `FIXA` · connect() faz handshake com get_version() antes de marcar conectado**
*Origem: fase 3 (D-04) · 2026-06-25*
O construtor do `ReqClient` sozinho não prova que a conexão funciona.
**Por quê:** sem o handshake o app se declarava conectado e só falhava no primeiro comando
real — o usuário via "conectado" e nada acontecia.

**D-13 · Conexão em thread por tentativa, descartada ao completar**
*Origem: fase 3 (D-01, D-02) · 2026-06-25*
`OBSConnectThread` emite `connected`/`failed`. Sem fila de comandos, sem thread persistente.
**Por quê:** a conexão bloqueava a UI. Thread por tentativa é o modelo mais simples que
resolve sem introduzir estado compartilhado.

**D-14 · Erros de OBS viram mensagem acionável, não stack trace**
*Origem: fase 3 (D-07, D-08) · 2026-06-25*
`_classificar_erro()` cobre 4 casos: conexão recusada, timeout, host inválido, senha errada.
Mensagem detalhada na aba OBS, versão resumida no rodapé. As duas funções vivem coladas no
mesmo arquivo de propósito, pra que mudar uma quebre a outra visivelmente.

---

## Modos de operação

**D-15 · `automatico` é o padrão de fábrica**
*Origem: fase 8 (D-01) · 2026-06-27*
**Por quê:** o objetivo é o usuário abrir, configurar gestos, apertar iniciar e pronto — sem
precisar entender que modos existem.

**D-16 · Modo `teste` bloqueia TODAS as ações**
*Origem: fase 8 (D-02) · 2026-06-27*
Sem OBS, sem hotkey, sem áudio. Sandbox puro pra calibrar gestos, com aviso explícito na
status bar.

**D-17 · `manual` conecta no OBS, sem VCam**
*Origem: fase 8 (D-04, D-05) · 2026-06-27*
Única diferença pro automático é a câmera virtual.
**Por quê:** fallback pra power user com conflito de driver de VCam.

**D-18 · Valores internos sem acento: `teste`, `manual`, `automatico`**
*Origem: fase 8 (D-09) · 2026-06-27*
Valores legados migram silenciosamente na leitura: `test` vira `teste`, `obs` vira
`automatico`. Valor desconhecido vira `automatico`.

---

## UI

**D-50 · A tradução de tecla saiu do widget, e o teste do AltGr passou a testar**
*2026-09-08 · commit `e371776`*

Com a captura de atalho existindo em duas telas — o `HotkeyLineEdit` de Widgets e a de QML
—, a regra não podia continuar dentro de uma delas. `ui/atalho_capturado.py` recebe números
e devolve texto; as duas chamam a mesma função.

**O que está em jogo é a defesa contra AltGr** (commit `8838edf`). Em layouts como o ABNT2,
Ctrl+Alt age como AltGr e o Qt entrega o caractere composto — `æ` no lugar de `z`. Gravar
isso produz um atalho que nunca casa com o registrado no OBS, e o usuário fica com um gesto
mudo, sem mensagem de erro. A proteção é usar o **código** da tecla, nunca o texto.

**O achado não foi a extração, foi o teste.** Ao validar por mutação, apagar a consulta ao
virtual key nativo — que *é* a proteção — deixava a suíte inteira verde.

O motivo: `test_altgr_nao_corrompe_a_tecla` montava o evento com `Qt.Key_Z`. Como 90 está na
faixa A-Z, a função retorna `"Z"` na primeira linha e **nunca chega** na consulta ao vk
nativo. O teste exercitava o caminho fácil e afirmava cobrir o difícil. Ele existia desde o
`8838edf` e ninguém tinha como notar, porque passava.

O caso real é outro: com AltGr o Qt reporta `Key_AE` (198), fora da faixa A-Z. Só o virtual
key nativo ainda diz `Z`. O teste agora usa esse caso; o antigo virou um segundo teste
explícito para o caminho fácil.

**Segundo achado, no mesmo lugar:** o QML entrega `int` na ponte e o `HotkeyLineEdit`
entrega enum do Qt. `int & KeyboardModifier` levanta `TypeError` — mas o caso das teclas era
pior: `17 in (Qt.Key_Control, ...)` podia dar `False` **em silêncio**, e o Ctrl deixaria de
contar como modificador sem erro aparecer. O módulo normaliza na fronteira, com teste
cobrindo os dois tipos.

**Regra que fica:** regra de domínio que duas telas precisam não mora em nenhuma das duas. E
teste de regressão que nunca entra no caminho que protege é decoração — a mutação é o que
separa um do outro.

**D-49 · A interface migra para QML, uma aba por vez, atrás de um contrato**
*2026-09-08 · commits `f638f45`, `afac56b`, `2c8ffac`, `89c7386`, `247ef41`*

O dono levantou a troca de framework em 2026-09-04 (B-21), sem decisão. A conversa que a
fechou foi em 2026-09-08, e o que decidiu não foi argumento — foi as duas versões da aba
Geral lado a lado (`teste/comparar_ui.py`).

**As queixas eram do toolkit, e verificáveis.** Dropdown, caixas, botões e redimensionamento:

- O `QComboBox` **não tinha seta**. O QSS fazia `::drop-down { border: none; width: 24px; }`
  e nunca estilizou `::down-arrow`. O campo de câmera não parecia um dropdown.
- O popup tinha cor mas nenhuma regra `::item`, então altura e respiro vinham do padrão
  nativo e não combinavam com a caixa.
- A 700px de largura a aba **cortava o conteúdo** e mostrava barra horizontal. Não é bug de
  implementação: `QLayout` não tem ponto de quebra, a ideia não existe no modelo.
- O indicador do `QCheckBox` tinha `image: none` — marcado se distinguia só pelo
  preenchimento roxo, sem marca nenhuma.
- 33 tamanhos fixos ou mínimos espalhados, incluindo `setMinimumSize(1200, 760)` na janela.

Esse é o modo de falhar característico do QSS: você sobrescreve um controle nativo em
pedaços, e todo pedaço esquecido fica com a aparência da plataforma. É a origem concreta da
sensação de "software de outra época".

**Custo zero de pacote.** O `QtQuick` já vem no PySide6 6.8.3 instalado. Nenhuma dependência
nova, nenhum MB a mais — o que também descartou as alternativas: Electron somaria ~150 MB
sobre os 480, e Tauri traria Rust, IPC e um empacotamento de Python notoriamente chato.

**O que destravou a migração foi um contrato, não a tela.** `ui/tabs/geral_contrato.py`
define o que a aba emite (intenções: `modoPedido`, `resolucaoPedida`, `cameraPedida`) e o
que ela oferece (`definir_cameras`, `definir_capacidades`, `definir_saude`). As duas
implementações o cumprem, e nenhum mixin conhece um widget de aba.

**Era isso que fazia a troca parecer cara — e o B-21 errou o diagnóstico.** Ele temia perder
a `QThread`, os `Signal` e o `QMediaDevices`. Nada disso se perde com QML, porque é tudo do
lado Python. O que prendia era o **alcance**: a janela mexia botão por botão
(`camera_device_combo.currentText()`, `resolution_buttons[r].setEnabled(...)`), então
qualquer implementação nova teria que fingir ser um `QComboBox`.

**`QQuickWidget` permite migrar uma aba por vez**, com o app rodando o tempo todo, em vez de
um "big bang" que só se prova no fim.

**A ordem importou:** a extração do D-47 veio antes. Sem um estado separado da tela, testar
QML exigiria reimplementar as regras junto, e a comparação seria entre duas coisas
diferentes. Com o estado pronto, a ponte Python↔QML ficou em ~190 linhas de tradução de
nomes.

**Três armadilhas de empacotamento, encontradas ao testar o caminho de falha:**

1. O `main.spec` só empacotava `assets/`. Os `.qml` são lidos do disco em execução, não
   importados como módulo, então o PyInstaller não os descobre. No `.exe` a interface nova
   não existiria.
2. O `QQuickWidget` **não levanta** quando o arquivo falta: registra o erro e fica em
   branco. O `try/except` do `setup_mixin` nunca era acionado, e o resultado da falha mais
   provável seria uma **aba vazia** — não o fallback que estava escrito. Os hosts passaram a
   conferir `status()` e levantar.
3. A queda só ia para o log de console, que não existe no `.exe`. O usuário veria a
   interface antiga achando que era a nova. Agora aparece no log da janela. Mesma regra do
   D-29 e do D-39: degradação silenciosa é pior que anunciada.

**E um vazamento:** quando a construção do QML falhava, a ponte era destruída mas continuava
inscrita no `EstadoApp`. Como `_notificar` engole exceção de ouvinte por desenho (D-47),
isso não virava falha — virava `Internal C++ object already deleted` no log a cada mudança
de estado. As pontes ganharam `desligar()`.

**A implementação de Widgets fica**, atrás de `GESTURENODE_UI=widgets`, enquanto o QML não
tiver rodado no pacote. Quando tiver, ela vira código paralelo que apodrece em silêncio, e a
pergunta certa passa a ser apagar ou manter — não é para ficar por inércia.

**D-48 · O estado do runtime é enum, não frase em português**
*2026-09-08 · commit `66da7f0`*

O painel de saúde decidia o estado do sistema lendo texto:

```python
if "falha ao iniciar câmera" in texto.lower():
obs_status_text = self.obs_status_label.text().lower()
```

A segunda linha é a grave: o painel lia o estado **de dentro do texto de um label**, ou
seja, o widget era a fonte da verdade. Renomear uma mensagem quebrava o painel em silêncio,
e nenhum teste pegaria — a mensagem "continua certa", só que ninguém mais a reconhece.

**A engine emite os dois canais, não um no lugar do outro.** `status_changed` continua
levando a frase para o log, e `evento` leva um `Evento` tipado para quem precisa decidir. O
log quer texto; o painel quer estado. Forçar um formato só era o erro.

A transição é uma função pura — `aplicar(saude, evento) → nova saúde` — testável sem
construir nada. E a aparência virou tabela por estado em vez de cadeia de `if`: acrescentar
um estado passa a ser uma linha, e esquecer um vira `KeyError` na hora, não silêncio.

**D-47 · O estado sai de dentro da UI e ganha aviso de mudança**
*2026-09-08 · commit `66da7f0`*

A UI decidia coisas que não eram da UI. O diagnóstico veio contado:

| Sintoma | Ocorrências |
|---|---|
| Guardas "isto é carga, não clique" (`blockSignals`, `_updating_gesture_form`) | 43 |
| Chamadas manuais de `salvar_config_automatico()` | 14 |
| UI escrevendo direto em atributo da engine em execução | 9 |
| UI chamando método privado da engine | 2 |
| Estado decidido lendo frase em português | 6 |

**Três causas, nenhuma delas o Qt:**

**Objeto-deus.** `MainWindow` herdava de sete mixins ao mesmo tempo — não módulos, um `self`
só dividido em arquivos. `ConfigMixin._load_ui_from_config` chamava métodos de três outros
mixins e mexia em widgets de um quarto. Não havia fronteira.

**O `config` era um dict cru fazendo papel de modelo.** Mutado no lugar de toda parte, sem
validação e sem notificação. Daí saem os dois primeiros números: os 14 saves existiam porque
nada avisava que o modelo mudou, e as 43 guardas porque `setChecked` não distingue "o
usuário clicou" de "estou carregando a config". **O D-41 não foi um bug que aconteceu — foi
a consequência inevitável do desenho**, e voltaria em cada campo novo.

**Regra de domínio na view.** `_init_config_schema` eram ~100 linhas de schema, migração de
campo legado e alias dentro de um mixin de UI. A mesma regra de clamp do `hold_time` existia
em três lugares, e ninguém tinha como notar que divergiram.

**O que saiu:** `core/config_schema.py`, `core/validacao_execucao.py`, `core/config_store.py`
e `core/estado_app.py`. Cerca de 400 linhas que nunca tocaram num widget — e que, enquanto
estiveram ali, **só rodavam se alguém abrisse a janela**, ou seja, nunca em teste.

**`EstadoApp` não importa Qt, e isso não é purismo.** Foi o que permitiu, dias depois,
adaptá-lo ao modelo de propriedades do QML traduzindo nomes em vez de reimplementar lógica
(D-49). Um modelo acoplado ao framework de tela teria que ser reescrito junto com ela.

**A guarda sobrou num lugar só.** `ui/vinculo.py` concentra o que estava espalhado — e
deliberadamente não virou sistema de binding declarativo: reimplementar binding sobre Qt
Widgets é escrever um mini-framework que o Qt Quick já traz pronto.

**Mudança de comportamento, uma:** `aplicar_config` lê `tempo_minimo` e `cooldown` de
`default_hold_time`/`default_cooldown`, como o `_setup()` já fazia no boot. O código antigo
os sobrescrevia com o binding do gesto **selecionado na tela**, fazendo o padrão global
depender de onde o usuário tinha clicado por último. Sem efeito visível, porque o schema
garante tempo próprio em todo binding — mas divergia do boot sem motivo.

**D-19 · Tema via QSS global em `ui/styles.py`, sem dependência nova**
*Origem: fase 15 (D-01, D-02) · 2026-07-01*
Aplicado uma vez em `main.py`. Recusado `qdarktheme` e similares.
**Por quê:** controle total sobre cada widget e zero dependência a mais num app que já
sofre pra empacotar.

**D-20 · Supressão de preview acontece na engine, não na UI**
*Origem: fase 15 (D-06, D-07) · 2026-07-01*
`GestureEngine.run()` pula o `frame_ready.emit()` quando `_preview_suprimido`. O loop de
captura e a detecção continuam rodando normalmente.
**Por quê:** minimizar a janela não pode parar de detectar gestos — só de desenhar.

---

## Config

**D-21 · `config.json` não é versionado**
*2026-09-03 · commit `c9d2271`*
Contém senha do WebSocket do OBS e paths da máquina. O app regenera completo no primeiro
boot via `_init_config_schema()`, então clone limpo funciona sem ele.
**Nota:** já estava no `.gitignore` desde a fase 1, mas seguia rastreado por falta de
`git rm --cached` — `.gitignore` não afeta o que já está no índice.

**D-29 · Config vai para `%APPDATA%` quando empacotado, e save que falha avisa**
*2026-09-03 · B-08*

**O problema.** `main.py` resolvia `Path(__file__).parent / "config.json"`. Congelado,
`__file__` aponta para o `_MEIPASS`, então o config era lido e gravado em
`dist\main\_internal\config.json` — dentro das entranhas do bundle. Funciona numa pasta de
usuário, mas instalado em `C:\Program Files\` o diretório não é gravável, o save falha, e
`_do_save_config` capturava o `OSError` e **apenas logava**. O usuário ajustava os gestos,
fechava o app e perdia tudo sem nenhum sinal.

Mesma família do bug que o D-22 resolveu (config indo parar em `C:\Windows\system32` ao
iniciar pelo atalho). Aquele foi corrigido só para o caso rodando do fonte; este é a versão
empacotada, e escapou porque ninguém tinha executado o `.exe` instalado.

**Onde o config mora agora** (`util/caminhos.py`):
- Rodando do código-fonte: ao lado do `main.py`, como sempre foi. Conveniente para
  desenvolver, e não muda nada para quem já usa assim.
- Empacotado: `%APPDATA%\OBS GestureNode\config.json`. Padrão do Windows, sempre gravável,
  e **sobrevive a reinstalar ou atualizar o app** — o que a pasta do bundle não faz.
- Sem `APPDATA` (ambiente atípico): cai para a home do usuário em vez de derrubar o app.

**Migração.** `migrar_config_legado()` copia do `_MEIPASS` para o novo destino no primeiro
boot. Sem isso, quem já usava o `.exe` perderia as configurações ao atualizar — trocaríamos
um jeito de perder dado por outro. Só copia se o destino ainda não existir: config atual
nunca é sobrescrito.

**Aviso de falha.** O save agora atualiza a status bar em toda falha e abre um diálogo
**uma vez por sessão**.
**Por quê uma vez só:** o autosave dispara a cada slider movido (debounce de 500ms do
D-22). Um modal por falha seria pior que o silêncio original — o usuário fecharia no
reflexo e ainda perderia o dado. A status bar continua avisando sempre, para quem dispensou
o diálogo.

**D-22 · Save do config é atômico e com debounce**
*Origem: fase 1 (ENG-05, ENG-06) · 2026-06-23*
`tempfile.mkstemp()` mais `os.replace()`, com path resolvido via `__file__`.
**Por quê:** mover sliders rápido corrompia o arquivo, e iniciar pelo atalho da área de
trabalho criava o config dentro de `C:\Windows\system32`.

---

## Dependências

**D-24 · `av` entra por faixa, não por pin exato — provisoriamente**
*2026-09-03*
A convenção do projeto (fase 1) é pinar tudo com `==` para máxima reprodutibilidade. `av`
entra como `av>=12,<15`, abrindo exceção.
**Por quê:** o `av` nunca esteve no `requirements.txt` — entrou no código junto com a
migração pro PyAV (`76607d8`) e a declaração ficou faltando. A versão realmente usada morreu
junto com o ambiente da máquina anterior, e a máquina atual não tem Python instalado, então
não há como verificar. Pinar um `==` que não pode ser testado é falsa precisão: se o palpite
errar, `pip install` falha e o app fica bloqueado pelo mesmo motivo de antes. Uma faixa
instala algo funcional e permite derivar o pin real de uma instalação que de fato subiu.
**Pendência:** após a primeira instalação limpa bem-sucedida, rodar `pip freeze` e converter
para `==`. Só então a convenção volta a ser respeitada.
**Mesmo caso:** `websocket-client`, importado direto em `obs_connect_thread.py` mas nunca
declarado. Fica sem pin exato para não conflitar com a resolução do `obsws-python`.

**D-26 · A VCam recebe resolução nativa; o esqueleto nela é escolha do usuário**
*2026-09-03 · resolve D-09*
Duas decisões separadas, porque são problemas diferentes:

**Resolução — não é escolha, é correção.** A câmera virtual passa a receber o frame de
captura nativo. `HandTracker.processar()` continua devolvendo a versão reduzida da
inferência, mas a engine agora guarda `frame_nativo` antes de chamar e usa cada um no
consumidor certo: reduzido no preview, nativo na VCam. Medido com listras de 4px em 1080p,
a variância do Laplaciano ia de 97503 para 390 no caminho antigo — 99,6% do detalhe fino
perdido (pior caso sintético; imagem real perde menos, mas o upscale era o mesmo).

**Esqueleto — é escolha, e do usuário do app.** Novo `camera.skeleton_na_vcam`, default
`False`, com checkbox próprio na aba Geral, independente do `show_skeleton` do preview.
**Por quê dois controles e não um:** o streamer quer o esqueleto no preview para calibrar e
quase nunca quer que o público veja. Um toggle único forçaria escolher entre calibrar às
cegas ou vazar as linhas na live. Como bônus, o label existente ("Mostrar esqueleto da mão
no preview") volta a ser verdadeiro — antes ele prometia preview e entregava preview + OBS,
porque os dois compartilhavam o mesmo frame.
**Nota sobre D-11:** a fase 15 tirou os controles de VCam da aba Geral. Este checkbox não
contraria aquilo: D-11 removeu plumbing técnico (device, modo), e este é escolha de conteúdo
— mora ao lado do checkbox de esqueleto, não numa seção de VCam.
**Custo:** `frame_nativo.copy()` só acontece quando o usuário liga o esqueleto na VCam e há
mão em quadro. Desligado (default), zero cópia extra.

**D-25 · `av` pinado em 14.2.0; `opencv-contrib-python` declarado para travar o `cv2`**
*2026-09-03 · commit `9e044dd`*
Fecha a pendência do D-24: a faixa vira `av==14.2.0`, e `opencv-contrib-python==4.10.0.84`
passa a ser declarado.
**Por quê (`av`):** não foi só "derivar o pin de uma instalação que subiu" — a faixa estava
ativamente quebrada. `av>=12,<15` resolve para a 14.4.x, e o PyAV parou de publicar wheel
cp310 para win_amd64 a partir da 14.3. O pip **não retrocede** para achar uma versão com
wheel: ele prefere a mais nova, aceita o sdist como candidato válido e tenta compilar,
morrendo em `Microsoft Visual C++ 14.0 or greater is required`. A 14.2.0 é a última com
wheel para o 3.10. Verificado: o wheel traz `dshow` compilado, que é o backend de
`core/camera.py`.
**Por quê (OpenCV):** `opencv-python` e `opencv-contrib-python` instalam no MESMO diretório
`cv2`, e o último a instalar vence. O contrib chega como transitivo do `mediapipe`, sem
limite superior, e resolvia para 5.0.0.93 — então `import cv2` respondia 5.0.0 enquanto o
`requirements.txt` pinava 4.10.0.84. O pin do `opencv-python` era decorativo. Travar os dois
na mesma versão upstream torna o resultado independente da ordem de instalação.
**O que NÃO motivou a mudança:** o OpenCV 5.0 não removeu nenhuma API usada pelo projeto
(`VideoWriter_fourcc` inclusive), e `numpy 2.2.6` convive com `mediapipe 0.10.14` sem erro
de import. Ambos foram testados. O alinhamento é por fidelidade ao pin declarado e por
evitar um major não auditado no caminho da câmera, não por quebra observada.
**Pitfalls:** ENV-01 e ENV-02.

---

## Processo

**D-23 · Planning enxuto: status em um lugar só, feito = SHA**
*2026-09-03*
O modelo GSD anterior (64 arquivos) foi arquivado em `.planning/archive/`. Ele falhou por
três motivos estruturais: status duplicado em frontmatter, ROADMAP e SUMMARYs, que
divergiram; fases renumeradas no meio (4 para 12, 5 para 14, 6 para 15), tornando "fase 9"
ambíguo; e custo alto de atualização, que fez o hábito de atualizar morrer. O resultado foi
um `STATE.md` afirmando `completed_phases: 0` enquanto o último commit dizia
`feat(phase-13-14-15)`, e 4 dos 5 todos "pendentes" já entregues.
**Regras novas:** status só no `STATE.md`; feito exige SHA de commit; plano detalhado é
descartável (vive em `active/`, morre ao fechar a fase); decisão e pitfall são duráveis.
**O que foi resgatado:** este arquivo e o `PITFALLS.md`. O resto está no archive.

---

**D-52 · A casca vira rail + barra, atrás de uma terceira opção de interface**
*2026-09-09*

O dono pediu uma remodelagem, não um conserto. A auditoria da UI tinha achado sete defeitos
(rótulo do cartão saindo fora, link azul, disabled invisível, foco por teclado inexistente,
cinco reprovações de contraste, ponto de quebra que nunca disparava, onboarding descrevendo
botões que não existem), e a conclusão foi que **nenhum deles era do framework** — eram
desta implementação. A moldura é que estava por terminar.

**A casca nova é a terceira opção, não a substituta.** `GESTURENODE_UI=novo` liga; sem
variável continua a de abas; `=widgets` continua a antiga. Mesma regra do D-49: enquanto
não rodar o bastante em uso real, quem estiver com ela precisa de caminho de volta que não
seja editar código.

**O que mudou de estrutura:**

- 4 abas horizontais → **rail vertical**. Aba estoura em ~6 itens; o rail vai a 10.
- Iniciar/Parar/Reiniciar → **um botão que alterna**. "Reiniciar" era parar+iniciar, e
  nunca era desabilitado. `restart_button` sobrevive só para o `connect` do mixin.
- Estado dito em 3 lugares (painel de saúde, `status_label`, `obs_footer_label` com emoji)
  → **2 chips na barra**. `_AdaptadorStatus` tem tabela explícita do que é estado: recado
  passageiro ("Config salva!") não pode apagar "Rodando" de um chip permanente.
- Log com lugar cativo na base → **gaveta de diagnóstico**.
- Diálogo modal "Escolher gestos ativos" → **interruptor no cartão**. Ativar e configurar
  param de ser dois lugares. `escolherGestosPedido` **não** é ligado nesta casca, de
  propósito: um `QDialog` cinza abrindo aqui seria a costura que ela existe para fechar.
- Grade e editor empilhados em 482px → **lado a lado**, com quebra em 860px.
- Modo como toggle + tooltip de 500ms → **cartões com a descrição visível**. É a decisão
  mais consequente do app e estava escondida atrás de hover.
- "Configurações Avançadas" (acordeão) → **removido**. Ele existia porque não cabia.

**Ela reaproveita as quatro pontes.** `PonteGeral`, `PonteGestos`, `PonteObs` e `PonteSobre`
já expunham estado real e intenções — a casca só desenha diferente. O que faltava virou
`PonteShell` (engine, preview, log, disparos) e `PonteOnboarding`. Os adaptadores no fim de
`ui/shell_novo.py` oferecem aos mixins a mesma superfície de sempre (`geral_tab`,
`log_view`, `start_button`…), então `camera_mixin`, `engine_mixin`, `obs_mixin` e
`health_mixin` não mudaram uma linha.

**O preview vai por `QQuickImageProvider`.** A engine emite `frame_ready` como sempre; o
quadro continua no mesmo processo, sem serialização. O contador na URL
(`image://preview/<n>`) é obrigatório — o Qt cacheia por URL e sem ele o preview congela no
primeiro quadro.

**O onboarding foi reescrito junto, e o texto era o problema maior.** O de Widgets mandava
clicar em "Selecionar gestos ativos" (o botão diz "Escolher gestos"), ajustar o "Tempo de
resposta" (o campo diz "Segurar por") e mexer no "modo da câmera virtual" dentro de
Configurações Avançadas — que só tinha resolução e FPS. E chamava Automático/Manual de modo
de câmera no passo 1 e de modo de operação no passo 2. Virou sobreposição da própria janela:
a interface que ele explica fica visível atrás enquanto ele a explica.

**O piso da janela baixou para 940x600 só nesta casca.** O 1200x760 é da interface de abas,
onde o `QFormLayout` não tem ponto de quebra. Num laptop de 1366x768 a barra de tarefas
deixa ~728px úteis: com piso 760 a janela **não cabe na tela** e o usuário não tem como
diminuir. Verificado de 1366x728 a 760x520 sem sobreposição.

**Contraste:** os cinco casos que reprovavam no WCAG AA passam. `textoApagado` 3.92→6.13,
placeholder 1.61→4.91, borda de controle 1.41→3.23. A borda subiu porque 1.4.11 pede 3:1
para o traço que identifica um controle; `bordaSutil` continua baixa por ser decorativa.

**Pitfalls:** QML-01 e QML-02.

---

**D-53 · Uma tela só para calibrar, e o preview lateral deixa de tentar servir aos dois usos**
*2026-09-09*

Ao usar a casca do D-52, o dono levantou três coisas na mesma frase: sobrava vazio no meio
das telas, os botões não aproveitavam o espaço, e o preview lateral era pequeno demais para
conferir a webcam.

**O vazio era teto de largura.** `TelaCamera`, `TelaObs` e `TelaSobre` limitavam a coluna a
860/760/820px para o texto não virar linha longa. Em tela larga isso deixava um buraco entre
o conteúdo e o painel de preview. O teto passou para o **texto**, que é quem tem limite de
leitura; cartões e botões usam a largura toda.

**O preview lateral não consegue servir aos dois usos.** Ele responde "está rodando?" de
relance, mas não responde "meu enquadramento está bom?" — para isso é preciso ver a mão do
tamanho que ela aparece. Alargar resolvia meio problema e roubava espaço da configuração.

A separação segue o uso real, que são dois: **configurar** (o preview é contexto) e
**calibrar** (a imagem é o assunto). Daí a tela `Ao vivo`, segunda no rail: câmera em
tamanho cheio, os chips do que a câmera está entregando, e o diagnóstico logo abaixo com a
saúde na mesma linha do log — quem está calibrando quer os dois juntos, não um em cada
ponta da janela.

**O painel lateral some enquanto ela está aberta.** A mesma câmera duas vezes na mesma tela
não ajuda ninguém e tira largura de quem importa. A gaveta de diagnóstico também não abre
lá, pelo mesmo motivo: o log já está na tela, fixo.

O painel lateral ainda cresceu de 372 para 440px, e o limiar em que ele cabe subiu de 1400
para 1460 — a largura extra não pode sair do conteúdo.
