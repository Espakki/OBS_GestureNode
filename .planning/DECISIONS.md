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
