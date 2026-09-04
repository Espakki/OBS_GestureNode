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
