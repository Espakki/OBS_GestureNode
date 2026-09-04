# ROADMAP — OBS GestureNode

---

## Milestone v1.1 "Stability & Polish"

**Milestone:** v1.1.0
**Baseline:** v1.0.0 (MVP taggeado)
**Granularity:** fine
**Phase convention:** sequential
**Total requirements:** 28 (7 phases)

---

### Phases (v1.1)

- [x] **Phase 1: Foundation** - Corrigir os 5 defeitos críticos e reparar dependências quebradas
- [x] **Phase 2: Engine & Camera** - Otimizar pipeline MediaPipe e estabilizar parâmetros de detecção (completed 2026-06-25)
- [x] **Phase 3: OBS Connection** - Tornar a conexão OBS confiável e não-bloqueante (completed 2026-06-25)
- [~] **Phase 4: Preview UX** - Absorvida na v1.2 (Phase 12) — nunca executada
- [~] **Phase 5: Onboarding & Config** - Absorvida na v1.2 (Phase 14) — nunca executada
- [~] **Phase 6: UI Visual Redesign** - Absorvida na v1.2 (Phase 15) — nunca executada
- [~] **Phase 7: Platform Abstraction** - Absorvida na v1.2 (Phase 16) — nunca executada

---

### Phase Details (v1.1)

#### Phase 1: Foundation

**Goal:** O app inicializa sem erros em qualquer ambiente e o config.json nunca é corrompido
**Mode:** mvp
**Depends on:** Nothing (primeira fase)
**Requirements:** ENG-03, ENG-04, ENG-05, ENG-06, DEP-01, DEP-02
**Success Criteria** (what must be TRUE):

  1. App iniciado via atalho na área de trabalho carrega o config.json corretamente (sem criar arquivo em C:\Windows\system32)
  2. Mover sliders rapidamente por 10 segundos não gera múltiplos arquivos temporários nem corrompe o config.json
  3. `pip install -r requirements.txt` em ambiente limpo instala todas as dependências sem erros, incluindo pygrabber
  4. Editar configurações em duas abas simultâneas não produz KeyError nem dispara a ação errada
  5. `GESTURE_ALIASES` retorna o mesmo dicionário independente de qual módulo é consultado

**Plans:** 5/5 plans executed — fase completa (UAT 2026-06-23)
**Wave 1**

- [x] 01-01-PLAN.md — Pinar dependências e adicionar pygrabber no requirements.txt (DEP-01, DEP-02)
- [x] 01-02-PLAN.md — Limpar config.json para template de install fresh (D-01, D-02)
- [x] 01-03-PLAN.md — Consolidar GESTURE_ALIASES em core/gesture_aliases.py (ENG-03)

**Wave 2** *(complete)*

- [x] 01-04-PLAN.md — Proteger gesture_bindings/mapa_cenas com threading.RLock (ENG-04)

**Wave 3** *(complete)*

- [x] 01-05-PLAN.md — Config path via __file__ + debounce 500ms e write atômico (ENG-05, ENG-06)

#### Phase 2: Engine & Camera

**Goal:** O pipeline de detecção roda a 28–35 FPS sustentados e para de forma limpa ao fechar
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** CAM-01, CAM-02, CAM-03, CAM-04, ENG-01, ENG-02
**Success Criteria** (what must be TRUE):

  1. Preview da câmera em 1080p exibe fluidez visivelmente maior que a v1.0.0 (sem travamentos de frame)
  2. Fechar o app ou reiniciar a câmera nunca exibe erro "câmera ocupada" na segunda abertura
  3. Gesto natural durante fala (ex: acenar para alguém) não dispara ação com hold_time padrão de 2.0s
  4. Usuário consegue reduzir hold_time para 0.5s nas configurações e o campo aceita o valor sem resetar
  5. Preview de câmera mantém frame rate estável mesmo quando MediaPipe demora mais que o usual em um frame

**Plans:** 5/5 plans complete

**Wave 1** *(paralelo — sem conflito de arquivos)*

- [x] 02-01-PLAN.md — Shutdown limpo da câmera: grab()+retrieve() + encerrar() resiliente + print→logger (CAM-04)
- [x] 02-02-PLAN.md — Parâmetros de estabilização detection_window_size=7, min_hits=5 + chaves no config (ENG-02)
- [x] 02-04-PLAN.md — hold_time mínimo 0.5s (slider/spinbox + 3 clamps) + nota de recomendação na UI (ENG-01)

**Wave 2**

- [x] 02-03-PLAN.md — Resize 640×480 (INTER_AREA) + MediaPipe lite (model_complexity=0, tracking 0.5); engine emite frame processado (CAM-01, CAM-02)

**Wave 3**

- [x] 02-05-PLAN.md — Teto de FPS de processamento time-based via process_fps + schema (CAM-03)

**UI hint**: yes

#### Phase 3: OBS Connection

**Goal:** A conexão com OBS nunca trava a UI e sempre informa claramente o que fazer quando falha
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** UX-04, OBS-01, UX-02, UX-03
**Success Criteria** (what must be TRUE):

  1. Clicar em "Conectar ao OBS" com OBS fechado não trava a janela do app (UI permanece responsiva)
  2. Indicador de status OBS (conectado / desconectado / tentando / erro) está visível em todas as abas da UI
  3. Erro "OBS não está aberto" exibe mensagem "Conexão recusada — abra o OBS Studio e ative o WebSocket Server"
  4. Erro de senha incorreta exibe mensagem "Senha incorreta — verifique as configurações do WebSocket no OBS"
  5. Estado "conectado" só aparece após o handshake get_version() ter sido bem-sucedido

**Plans:** 3/3 plans complete

**Wave 1**

- [x] 03-01-PLAN.md — OBSConnectThread(QThread) + handshake get_version() em OBSController.connect() + classificador de erros (OBS-01, UX-04, UX-03)

**Wave 2** *(paralelo — arquivos disjuntos)*

- [x] 03-02-PLAN.md — Botão "Testar conexão" não-bloqueante + label de status OBS no rodapé + slots de resultado (UX-04, UX-02, UX-03)
- [x] 03-03-PLAN.md — engine._connect_obs() com handshake + mensagens de erro classificadas reutilizando _classificar_erro (OBS-01, UX-03, UX-02)

**UI hint**: yes

#### Phase 4: Preview UX

> **Absorvida na v1.2 (Phase 12)** — nunca executada na v1.1. Requisitos UX-05 e UX-06 continuam ativos em v1.2.

#### Phase 5: Onboarding & Config

> **Absorvida na v1.2 (Phase 14)** — nunca executada na v1.1. Requisitos UX-07, UX-08, UX-09 continuam ativos em v1.2.

#### Phase 6: UI Visual Redesign

> **Absorvida na v1.2 (Phase 15)** — nunca executada na v1.1. Requisitos UI-01, UI-02, UI-03, UI-04 continuam ativos em v1.2.

#### Phase 7: Platform Abstraction

> **Absorvida na v1.2 (Phase 16)** — nunca executada na v1.1. Requisitos PLT-01, PLT-02, PLT-03 continuam ativos em v1.2.

---

### Progress (v1.1)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 5/5 | Complete | 2026-06-23 |
| 2. Engine & Camera | 5/5 | Complete | 2026-06-25 |
| 3. OBS Connection | 3/3 | Complete | 2026-06-25 |
| 4. Preview UX | — | Absorbed into v1.2 Phase 12 | — |
| 5. Onboarding & Config | — | Absorbed into v1.2 Phase 14 | — |
| 6. UI Visual Redesign | — | Absorbed into v1.2 Phase 15 | — |
| 7. Platform Abstraction | — | Absorbed into v1.2 Phase 16 | — |

---

### Coverage Map (v1.1)

| REQ-ID | Phase | Category |
|--------|-------|----------|
| ENG-03 | Phase 1 | Engine Foundation |
| ENG-04 | Phase 1 | Engine Foundation |
| ENG-05 | Phase 1 | Engine Foundation |
| ENG-06 | Phase 1 | Engine Foundation |
| DEP-01 | Phase 1 | Engine Foundation |
| DEP-02 | Phase 1 | Engine Foundation |
| CAM-01 | Phase 2 | Performance de Camera |
| CAM-02 | Phase 2 | Performance de Camera |
| CAM-03 | Phase 2 | Performance de Camera |
| CAM-04 | Phase 2 | Performance de Camera |
| ENG-01 | Phase 2 | Engine de Deteccao |
| ENG-02 | Phase 2 | Engine de Deteccao |
| UX-04 | Phase 3 | Conexao OBS |
| OBS-01 | Phase 3 | Conexao OBS |
| UX-02 | Phase 3 | Conexao OBS |
| UX-03 | Phase 3 | Conexao OBS |
| UX-05 | Phase 12 (v1.2) | Preview e Feedback Visual |
| UX-06 | Phase 12 (v1.2) | Preview e Feedback Visual |
| UX-07 | Phase 14 (v1.2) | Configuracao e UX |
| UX-08 | Phase 14 (v1.2) | Configuracao e UX |
| UX-09 | Phase 14 (v1.2) | Configuracao e UX |
| UI-01 | Phase 15 (v1.2) | UI Visual Redesign |
| UI-02 | Phase 15 (v1.2) | UI Visual Redesign |
| UI-03 | Phase 15 (v1.2) | UI Visual Redesign |
| UI-04 | Phase 15 (v1.2) | UI Visual Redesign |
| PLT-01 | Phase 16 (v1.2) | Platform Abstraction |
| PLT-02 | Phase 16 (v1.2) | Platform Abstraction |
| PLT-03 | Phase 16 (v1.2) | Platform Abstraction |

---

---

## Milestone v1.2 "Features & Polish"

**Milestone:** v1.2.0
**Baseline:** v1.1 (Phases 1–3 completas)
**Granularity:** fine
**Phase convention:** sequential
**Total requirements:** 27 (9 phases, Phases 8–16)

---

### Phases (v1.2)

- [ ] **Phase 8: Modos de Operação** - Renomear/adicionar os 3 modos com comportamentos WebSocket/VCam distintos
- [ ] **Phase 9: HandTracker API Refactor** - Refatorar HandTracker.processar() para list[dict] por mão; commit atômico com GestureEngine
- [ ] **Phase 10: Config Schema + Detection Engine** - config.json v2 com max_maos/combined_bindings; pipeline de detecção de par no engine
- [ ] **Phase 11: Combined Gesture UI + Presets** - Aba Gestos com seção combinada; CombinedGestureDialog; 6 presets de streamer
- [ ] **Phase 12: Preview Overlay** - Overlay de gesto + barra de hold time + flash no preview; variantes 1 mão e 2 mãos
- [ ] **Phase 13: Camera Settings** - Sub-modos Padrão/Personalizado; enumeração de formatos DirectShow; badge de lag passivo; sugestão guiada
- [ ] **Phase 14: Onboarding & Config UX** - Dialog primeira execução 4 passos; validação inline; feedback de gesto durante configuração
- [ ] **Phase 15: UI Visual Redesign** - Dark mode padrão; paleta consistente; hover states; componentização de gesture cards
- [ ] **Phase 16: Platform Abstraction** - platform/_windows.py + _protocol.py; ActionManager com injeção de dependência

---

### Phase Details (v1.2)

#### Phase 8: Modos de Operação

**Goal:** Os três modos de operação têm comportamentos WebSocket/VCam distintos e a seleção persiste entre sessões
**Depends on:** Phase 3 (OBS Connection)
**Requirements:** MODE-01, MODE-02, MODE-03, MODE-04
**Files affected:** ui/tabs/geral_tab.py, ui/main_window.py, engine/gesture_engine.py, config.json
**Success Criteria** (what must be TRUE):

  1. Modo "Teste": câmera roda e gestos aparecem no preview, mas nenhuma ação OBS ou hotkey é executada — mesmo com OBS aberto
  2. Modo "Manual": atalhos de teclado e áudio funcionam; VCam output permanece desativado; usuário decide quando conectar ao OBS
  3. Modo "Automático": conexão WebSocket e VCam output iniciam automaticamente ao abrir o app sem clique adicional do usuário
  4. Reiniciar o app após trocar de modo carrega o mesmo modo selecionado — seleção não retorna ao padrão
  5. Primeira execução inicia no modo "Teste" sem exigir OBS aberto *(NOTE: substituído por D-01 — padrão de fábrica é "automatico")*

**Plans:** 3/4 plans executed

**Wave 1** *(paralelo — arquivos disjuntos)*

- [x] 08-01-PLAN.md — Matriz de comportamento no backend: engine (_connect_obs manual/automatico, VCam só automatico, status Teste) + ActionManager bloqueia ações em Teste (MODE-01, MODE-02, MODE-03)
- [x] 08-02-PLAN.md — Aba Geral: botão Manual + renomear OBS→Automático, tooltips, mode_help_label e set_mode para 3 modos (MODE-01, MODE-02, MODE-03)

**Wave 2**

- [x] 08-03-PLAN.md — main_window: migração silenciosa do modo + padrão automatico, wiring dos 3 botões, VCam por modo, health/validação (MODE-04, MODE-01, MODE-02, MODE-03)

**Wave 3** *(checkpoint)*

- [ ] 08-04-PLAN.md — Verificação humana da matriz de comportamento e persistência entre sessões (MODE-01, MODE-02, MODE-03, MODE-04)

**UI hint**: yes

#### Phase 9: HandTracker API Refactor

**Goal:** HandTracker.processar() retorna list[dict] por mão com handedness correto; GestureEngine atualizado atomicamente; nenhuma regressão de 1 mão
**Depends on:** Phase 8
**Requirements:** GES-01, GES-02
**CRITICAL:** hand_tracker.py e gesture_engine.py devem ser commitados atomicamente — a mudança de API quebra o engine se os arquivos não forem atualizados juntos
**Success Criteria** (what must be TRUE):

  1. Levantar a mão direita física exibe label "Right" no preview; mão esquerda exibe "Left" — sem inversão com câmera espelhada
  2. Modo "1 mão" funciona identicamente ao comportamento anterior da v1.1 — nenhuma regressão observável
  3. Com uma mão saindo e entrando do frame em modo "2 mãos", o engine não lança exceção nem congela o preview

**Plans:** TBD

#### Phase 10: Config Schema + Combined Gesture Detection Engine

**Goal:** config.json v2 com max_maos e combined_bindings; configs v1.1 carregam sem exceção; GestureDetector.detectar_par() implementado; pipeline de 2 mãos ativo no engine
**Depends on:** Phase 9
**Requirements:** GES-06, GES-07
**Success Criteria** (what must be TRUE):

  1. Carregar config.json v1.1 (sem max_maos) inicia o app em modo "1 mão" sem exceção nem perda de bindings existentes
  2. Gesto combinado dispara somente quando AMBAS as mãos mantêm seus gestos pelo hold_time completo — uma mão sozinha não dispara
  3. config.json salvo contém config_version: 2, max_maos e combined_bindings sem sobrescrever bindings de 1 mão

**Plans:** TBD

#### Phase 11: Combined Gesture UI + Presets

**Goal:** Usuário configura gestos combinados via UI com 6 presets pré-definidos ou combinações personalizadas
**Depends on:** Phase 10
**Requirements:** GES-03, GES-04, GES-05
**Success Criteria** (what must be TRUE):

  1. Aba Gestos exibe seção "Gestos Combinados" com 6 presets quando modo "2 mãos" está ativo — seção oculta no modo "1 mão"
  2. Ativar preset "Go Live (mão aberta + mão aberta)" e salvar registra chave canônica "OPEN_PALM+OPEN_PALM" no config.json — não o nome de display
  3. Dialog de configuração personalizada exibe qual gesto está sendo detectado em cada mão em tempo real durante a configuração
  4. Combinação personalizada configurada aparece listada na seção de gestos combinados após salvar

**Plans:** TBD
**UI hint**: yes

#### Phase 12: Preview Overlay

**Goal:** Usuário vê em tempo real qual gesto está sendo detectado e o progresso de hold time — com variantes para 1 e 2 mãos
**Depends on:** Phase 9
**Requirements:** UX-05, UX-06
**Success Criteria** (what must be TRUE):

  1. Preview exibe nome do gesto detectado sobreposto no frame em modo "1 mão"
  2. Em modo "2 mãos", labels "Esquerda: [Gesto]" e "Direita: [Gesto]" aparecem posicionados espacialmente nos lados correspondentes do frame
  3. Barra de progresso de hold time cresce enquanto o gesto é mantido e desaparece ao soltar — uma barra por mão no modo "2 mãos"
  4. Flash visual no preview confirma o momento exato em que a ação é disparada

**Plans:** TBD
**UI hint**: yes

#### Phase 13: Camera Settings

**Goal:** Usuário controla configurações de câmera via sub-modos Padrão/Personalizado; badge de latência passivo informa estado sem interromper o fluxo
**Depends on:** Phase 8
**Requirements:** CAM-05, CAM-06, CAM-07, CAM-08
**NOTE:** CAP_MSMF e virtual cam relay são explicitamente excluídos — não implementar como itens desta fase
**Success Criteria** (what must be TRUE):

  1. Sub-modo "Padrão do sistema" deixa câmera negociar formato automaticamente — nenhuma opção manual exposta ao usuário
  2. Sub-modo "Personalizado" exibe lista real de resoluções, FPS e formatos (YUY2, MJPEG) suportados pelo dispositivo via DirectShow/pygrabber
  3. Badge de latência (verde/amarelo/vermelho) aparece na aba Geral após os primeiros 30 frames — sem modal, sem interrupção do fluxo
  4. Com lag > 80ms e sub-modo Personalizado disponível, sugestão inline aparece recomendando trocar para YUY2 em resolução menor

**Plans:** TBD
**UI hint**: yes

#### Phase 14: Onboarding & Config UX

**Goal:** Usuário novo configura o primeiro gesto sem ler documentação; campos de configuração fornecem feedback imediato em tempo real
**Depends on:** Phase 11, Phase 12
**Requirements:** UX-07, UX-08, UX-09
**Success Criteria** (what must be TRUE):

  1. Na primeira execução, dialog de 4 passos abre automaticamente: (1) verificar câmera, (2) selecionar modo, (3) conectar OBS se necessário, (4) configurar primeiro gesto
  2. Campo de arquivo .wav exibe erro inline "Arquivo não encontrado" imediatamente ao sair do campo com caminho inválido
  3. Campo de hotkey exibe a combinação capturada em tempo real enquanto o usuário pressiona as teclas
  4. Ao abrir configuração de um gesto, preview ao vivo mostra qual gesto está sendo detectado naquele momento

**Plans:** TBD
**UI hint**: yes

#### Phase 15: UI Visual Redesign

**Goal:** A interface tem identidade visual consistente com dark mode nativo adequado para ambiente de streaming
**Depends on:** Phase 14
**Requirements:** UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):

  1. Dark mode ativo por padrão em todas as abas — nenhum fundo branco ou cinza genérico visível em nenhuma aba
  2. Todas as abas usam a mesma paleta de cores, tipografia e espaçamento — zero inconsistências visuais entre abas
  3. Hover states e transições visíveis em todos os controles interativos — botões, sliders, toggles
  4. Cards de configuração de gesto componentizados — adicionar ou remover um gesto não quebra o layout dos outros

**Plans:** TBD
**UI hint**: yes

#### Phase 16: Platform Abstraction

**Goal:** Todo código Windows-específico está isolado em platform/_windows.py sem imports diretos fora do módulo; ActionManager usa injeção de dependência
**Depends on:** Phase 15 (maior superfície de merge conflict — sempre última)
**Requirements:** PLT-01, PLT-02, PLT-03
**NOTE:** Sempre última — maior superfície de merge conflict com qualquer feature ainda em andamento
**Success Criteria** (what must be TRUE):

  1. Nenhum import de winsound, ctypes, cv2.CAP_DSHOW ou pygrabber aparece fora de platform/_windows.py
  2. ActionManager recebe AudioBackend e InputBackend no construtor — não referencia winsound ou ctypes diretamente
  3. Módulo platform/ contém _protocol.py com interfaces (AudioBackend, InputBackend, CameraEnumerator) e _windows.py com implementações Windows
  4. App funciona identicamente ao comportamento da Phase 15 após refatoração — nenhuma regressão observável pelo usuário

**Plans:** TBD

---

### Progress (v1.2)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. Modos de Operação | 3/4 | In Progress|  |
| 9. HandTracker API Refactor | 0/? | Not started | - |
| 10. Config Schema + Detection Engine | 0/? | Not started | - |
| 11. Combined Gesture UI + Presets | 0/? | Not started | - |
| 12. Preview Overlay | 0/? | Not started | - |
| 13. Camera Settings | 0/? | Not started | - |
| 14. Onboarding & Config UX | 0/? | Not started | - |
| 15. UI Visual Redesign | 0/? | Not started | - |
| 16. Platform Abstraction | 0/? | Not started | - |

---

### Coverage Map (v1.2)

| REQ-ID | Phase | Category |
|--------|-------|----------|
| MODE-01 | Phase 8 | Modos de Operacao |
| MODE-02 | Phase 8 | Modos de Operacao |
| MODE-03 | Phase 8 | Modos de Operacao |
| MODE-04 | Phase 8 | Modos de Operacao |
| GES-01 | Phase 9 | Deteccao de 2 Maos |
| GES-02 | Phase 9 | Deteccao de 2 Maos |
| GES-06 | Phase 10 | Deteccao de 2 Maos |
| GES-07 | Phase 10 | Deteccao de 2 Maos |
| GES-03 | Phase 11 | Deteccao de 2 Maos |
| GES-04 | Phase 11 | Deteccao de 2 Maos |
| GES-05 | Phase 11 | Deteccao de 2 Maos |
| UX-05 | Phase 12 | Preview e Feedback Visual |
| UX-06 | Phase 12 | Preview e Feedback Visual |
| CAM-05 | Phase 13 | Configuracoes de Camera |
| CAM-06 | Phase 13 | Configuracoes de Camera |
| CAM-07 | Phase 13 | Configuracoes de Camera |
| CAM-08 | Phase 13 | Configuracoes de Camera |
| UX-07 | Phase 14 | Configuracao e UX |
| UX-08 | Phase 14 | Configuracao e UX |
| UX-09 | Phase 14 | Configuracao e UX |
| UI-01 | Phase 15 | UI Visual Redesign |
| UI-02 | Phase 15 | UI Visual Redesign |
| UI-03 | Phase 15 | UI Visual Redesign |
| UI-04 | Phase 15 | UI Visual Redesign |
| PLT-01 | Phase 16 | Platform Abstraction |
| PLT-02 | Phase 16 | Platform Abstraction |
| PLT-03 | Phase 16 | Platform Abstraction |

**Coverage: 27/27 v1.2 requirements mapped**

---

*Last updated: 2026-06-26 — milestone v1.2 "Features & Polish" roadmap criado*
