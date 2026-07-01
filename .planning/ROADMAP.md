# ROADMAP — OBS GestureNode v1.1 "Stability & Polish"

**Milestone:** v1.1.0
**Baseline:** v1.0.0 (MVP taggeado)
**Granularity:** fine
**Phase convention:** sequential
**Total requirements:** 28 (7 phases)

---

## Phases

- [x] **Phase 1: Foundation** - Corrigir os 5 defeitos críticos e reparar dependências quebradas
- [ ] **Phase 2: Engine & Camera** - Otimizar pipeline MediaPipe e estabilizar parâmetros de detecção
- [ ] **Phase 3: OBS Connection** - Tornar a conexão OBS confiável e não-bloqueante
- [ ] **Phase 4: Preview UX** - Adicionar feedback visual de gesto detectado no preview da câmera
- [ ] **Phase 5: Onboarding & Config** - Implementar onboarding de primeira execução e validação inline
- [ ] **Phase 6: UI Visual Redesign** - Redesenhar identidade visual, layout e componentização da interface
- [ ] **Phase 7: Platform Abstraction** - Isolar código Windows-específico atrás de interfaces de plataforma

---

## Phase Details

### Phase 1: Foundation

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

### Phase 2: Engine & Camera

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

**Plans:** TBD
**UI hint**: yes

### Phase 3: OBS Connection

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

**Plans:** TBD
**UI hint**: yes

### Phase 4: Preview UX

**Goal:** O usuário vê em tempo real qual gesto está sendo detectado e quando ele vai disparar
**Mode:** mvp
**Depends on:** Phase 2, Phase 3
**Requirements:** UX-05, UX-06
**Success Criteria** (what must be TRUE):

  1. Preview da câmera exibe o nome do gesto atual (ex: "THUMBS_UP") sobreposto diretamente no frame
  2. Barra de progresso de hold time cresce visualmente enquanto o gesto é mantido e some quando solto
  3. Flash visual ou highlight no preview confirma visualmente o momento exato em que a ação é disparada

**Plans:** TBD
**UI hint**: yes

### Phase 5: Onboarding & Config

**Goal:** Um usuário novo consegue configurar o primeiro gesto sem ler documentação
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** UX-07, UX-08, UX-09
**Success Criteria** (what must be TRUE):

  1. Na primeira execução, dialog de boas-vindas guia o usuário pelos 4 passos: câmera → OBS → testar gesto → configurar ação
  2. Campo de arquivo .wav exibe erro inline "Arquivo não encontrado" imediatamente ao sair do campo com caminho inválido
  3. Campo de hotkey exibe a combinação capturada em tempo real enquanto o usuário pressiona as teclas
  4. Aba de configuração de gesto exibe feedback visual quando um gesto é detectado durante a configuração

**Plans:** TBD
**UI hint**: yes

### Phase 6: UI Visual Redesign

**Goal:** A interface reflete a identidade visual de um app profissional para streamers — consistente, dark, e polida
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):

  1. Todas as abas usam a mesma paleta de cores, tipografia e espaçamento — zero inconsistências visuais entre abas
  2. Dark mode ativo por padrão; app parece nativo no ambiente de um streamer (sem fundo branco/cinza genérico)
  3. Hover states e transições visíveis em todos os controles interativos (botões, sliders, toggles)
  4. Cards de configuração de gesto são componentizados — adicionar/remover um gesto não quebra o layout

**Plans:** TBD
**UI hint**: yes

### Phase 7: Platform Abstraction

**Goal:** Todo código Windows-específico está isolado em platform/_windows.py, sem imports diretos fora do módulo
**Mode:** mvp
**Depends on:** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6
**Requirements:** PLT-01, PLT-02, PLT-03
**Success Criteria** (what must be TRUE):

  1. Nenhum `import winsound`, `import ctypes`, `cv2.CAP_DSHOW` ou `pygrabber` aparece fora de `platform/_windows.py`
  2. `ActionManager` recebe `AudioBackend` e `InputBackend` no construtor e não referencia winsound ou ctypes diretamente
  3. Módulo `platform/` contém `_protocol.py` com interfaces definidas e `_windows.py` com todas as implementações Windows
  4. App funciona identicamente ao comportamento da Phase 6 após a refatoração (sem regressões observáveis)

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/5 | In Progress|  |
| 2. Engine & Camera | 0/? | Not started | - |
| 3. OBS Connection | 0/? | Not started | - |
| 4. Preview UX | 0/? | Not started | - |
| 5. Onboarding & Config | 0/? | Not started | - |
| 6. UI Visual Redesign | 0/? | Not started | - |
| 7. Platform Abstraction | 0/? | Not started | - |

---

## Coverage Map

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
| UX-05 | Phase 4 | Preview e Feedback Visual |
| UX-06 | Phase 4 | Preview e Feedback Visual |
| UX-07 | Phase 5 | Configuracao e UX |
| UX-08 | Phase 5 | Configuracao e UX |
| UX-09 | Phase 5 | Configuracao e UX |
| UI-01 | Phase 6 | UI Visual Redesign |
| UI-02 | Phase 6 | UI Visual Redesign |
| UI-03 | Phase 6 | UI Visual Redesign |
| UI-04 | Phase 6 | UI Visual Redesign |
| PLT-01 | Phase 7 | Platform Abstraction |
| PLT-02 | Phase 7 | Platform Abstraction |
| PLT-03 | Phase 7 | Platform Abstraction |

**Coverage: 28/28 v1 requirements mapped**

---

*Last updated: 2026-06-22*
