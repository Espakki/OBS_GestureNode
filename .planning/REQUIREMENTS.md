# Requirements — OBS GestureNode v1.1 "Stability & Polish"

**Versão:** v1.1.0
**Baseline:** v1.0.0 (MVP taggeado)
**Escopo:** Estabilização, performance de câmera, e UX polish — sem expansão de features

---

## v1 Requirements

### Categoria: Engine Foundation (Correções Críticas)

Pré-requisitos bloqueantes. Devem ser implementados antes de qualquer outra coisa.

- [ ] **ENG-03**: `GESTURE_ALIASES` consolidado em fonte única (`core/gesture_aliases.py`) — eliminar as 3 cópias divergentes em `gesture_engine.py`, `main_window.py`, `gesture_detector.py`
- [ ] **ENG-04**: Acesso a `gesture_bindings` e `mapa_cenas` protegido por `threading.RLock` — eliminar race condition entre main thread e engine thread
- [ ] **ENG-05**: Config `config.json` carregado por caminho absoluto derivado de `__file__` — eliminar dependência de CWD
- [ ] **ENG-06**: `salvar_config_automatico()` com debounce de 500ms + write atômico (temp file + `os.replace()`) — eliminar risco de corrupção em crash
- [ ] **DEP-01**: `pygrabber` adicionado ao `requirements.txt` com versão fixada — corrigir install quebrado em ambientes novos
- [ ] **DEP-02**: Todas as dependências (`PySide6`, `opencv-python`, `pyvirtualcam`, `obsws-python`, `keyboard`) com versões fixadas no `requirements.txt`

### Categoria: Performance de Câmera

- [ ] **CAM-01**: Engine redimensiona o frame para 640×480 antes de passar ao MediaPipe, independente da resolução de captura — separação entre resolução de exibição e resolução de processamento
- [ ] **CAM-02**: Parâmetros do MediaPipe Hands atualizados: `model_complexity=0` (lite), `min_tracking_confidence=0.5` — ganho de 40–55% de FPS sem perda de precisão para os 8 gestos geométricos
- [ ] **CAM-03**: Loop da engine com teto de FPS de processamento configurável (via `process_fps` no config) — desacoplar frame rate de captura do frame rate de inferência
- [x] **CAM-04**: `GestureEngine.stop()` libera câmera garantidamente antes de retornar — substituir `cap.read()` por `grab()` + `retrieve()` para evitar bloqueio no stop

### Categoria: Engine de Detecção

- [ ] **ENG-01**: `hold_time` configurável com mínimo de 0.5s e padrão de 2.0s — UI exibe nota indicando que 2.0s é o recomendado para streaming ao vivo (proteção contra gestos acidentais durante fala)
- [x] **ENG-02**: Parâmetros de estabilização ajustados: `detection_window_size=7`, `detection_min_hits=5` (71%) — redução de falsos positivos mantendo responsividade

### Categoria: Conexão OBS

- [x] **UX-02**: Indicador de estado da conexão OBS sempre visível na UI (conectado / desconectado / erro / tentando)
- [x] **UX-03**: Erros de conexão exibem mensagem acionável classificada por tipo: "Conexão recusada — OBS não está aberto", "Timeout — verifique o IP/porta", "Senha incorreta — verifique as configurações do WebSocket"
- [x] **UX-04**: Conexão e reconexão com OBS executadas em `QThread` separado — UI thread nunca bloqueada durante operações de rede
- [x] **OBS-01**: `OBSController.connect()` verifica handshake com `get_version()` antes de setar `connected = True` — eliminar falso positivo de conexão

### Categoria: Preview e Feedback Visual

- [ ] **UX-05**: Preview da câmera exibe overlay com nome do gesto detectado atualmente (desenhado diretamente no frame OpenCV antes de `frame_ready.emit()`)
- [ ] **UX-06**: Preview exibe barra de progresso de hold time — usuário vê o gesto "carregando" até o threshold; flash visual confirma disparo

### Categoria: Configuração e UX

- [ ] **UX-07**: Campos de configuração com validação inline: arquivo `.wav` exibe erro se não encontrado; hotkey exibe combinação capturada em tempo real
- [ ] **UX-08**: Feedback visual quando um gesto é detectado enquanto o usuário está na aba de configuração — facilita ajuste do threshold
- [ ] **UX-09**: Dialog de primeira execução (`first_run: true` no config) com checklist de 4 passos: (1) verificar câmera, (2) conectar OBS, (3) testar detecção de gesto, (4) configurar primeira ação

### Categoria: UI Visual Redesign

- [ ] **UI-01**: Identidade visual consistente — paleta de cores definida, tipografia uniforme, tema dark mode como padrão (adequado para streamers em ambiente de studio)
- [ ] **UI-02**: Layout e espaçamento revisados — proporções de abas balanceadas, alinhamento de elementos em grid consistente, hierarquia visual clara entre seções
- [ ] **UI-03**: Animações e transições suaves — hover states nos controles, feedback visual em mudanças de estado (conectado/desconectado), transições entre abas
- [ ] **UI-04**: Componentização — widgets reutilizáveis para elementos repetidos (cards de configuração de gesto, indicadores de status, botões de ação) — eliminar inconsistências visuais entre abas

### Categoria: Platform Abstraction (Preparação para Linux v2.0)

- [ ] **PLT-01**: Módulo `platform/` criado com `_protocol.py` (interfaces `AudioBackend`, `InputBackend`, `CameraEnumerator`) e `_windows.py` (implementações atuais)
- [ ] **PLT-02**: Todo código platform-específico (`winsound`, `ctypes`, `cv2.CAP_DSHOW`, `pygrabber`) movido para `platform/_windows.py` — nenhum import direto fora do módulo de plataforma
- [ ] **PLT-03**: `ActionManager` recebe `AudioBackend` e `InputBackend` por injeção de dependência — sem acoplamento direto a implementações Windows

---

## v2 Requirements (Deferred)

Requisitos identificados mas fora do escopo de v1.1:

- Suporte Linux com paridade total (audio cross-platform via `sounddevice`, input via `pynput`, virtual cam via v4l2loopback)
- Novos gestos além dos 8 atuais
- Combinações de ações por gesto (segurar vs. soltar, múltiplas ações)
- Reconexão automática ao OBS após queda de conexão
- Auto-update do aplicativo
- Cloud sync de configurações

---

## Out of Scope (v1.1 e além)

- Plugin system / extensibilidade por terceiros — arquitetura não justifica ainda
- Aprendizado de gesto customizado (ML training) — fora do escopo do projeto
- Suporte mobile/web — app desktop por definição
- Multi-câmera simultânea — caso de uso não identificado
- Streaming de gestos para outros apps além do OBS — feature creep

---

## Traceability

| REQ-ID | Phase | Phase Name | Prioridade | Status | Fonte |
|--------|-------|------------|------------|--------|-------|
| ENG-03 | 1 | Foundation | CRÍTICO | Complete | CONCERNS.md + PITFALLS.md |
| ENG-04 | 1 | Foundation | CRÍTICO | Complete | CONCERNS.md + PITFALLS.md CRITICAL-01 |
| ENG-05 | 1 | Foundation | CRÍTICO | Complete | PITFALLS.md CRITICAL-05 |
| ENG-06 | 1 | Foundation | CRÍTICO | Complete | PITFALLS.md CRITICAL-04 |
| DEP-01 | 1 | Foundation | ALTO | Complete | CONCERNS.md (missing requirement) |
| DEP-02 | 1 | Foundation | ALTO | Complete | STACK.md (dependency risks) |
| CAM-01 | 2 | Engine & Camera | ALTO | Pending | STACK.md + USER (problema 1080p) |
| CAM-02 | 2 | Engine & Camera | ALTO | Pending | STACK.md (model_complexity=0) |
| CAM-03 | 2 | Engine & Camera | MÉDIO | Pending | STACK.md (process_fps cap) |
| CAM-04 | 2 | Engine & Camera | CRÍTICO | Complete | PITFALLS.md CRITICAL-03 |
| ENG-01 | 2 | Engine & Camera | ALTO | Pending | USER (2.0s padrão streaming) + FEATURES.md (0.5s mínimo) |
| ENG-02 | 2 | Engine & Camera | MÉDIO | Complete | FEATURES.md (detection params) |
| UX-04 | 3 | OBS Connection | CRÍTICO | Pending | PITFALLS.md MODERATE-03 |
| OBS-01 | 3 | OBS Connection | CRÍTICO | Pending | PITFALLS.md CRITICAL-02 |
| UX-02 | 3 | OBS Connection | ALTO | Pending | USER + FEATURES.md |
| UX-03 | 3 | OBS Connection | ALTO | Pending | USER + FEATURES.md |
| UX-05 | 4 | Preview UX | ALTO | Pending | USER + FEATURES.md |
| UX-06 | 4 | Preview UX | ALTO | Pending | FEATURES.md (hold progress bar) |
| UX-07 | 5 | Onboarding & Config | MÉDIO | Pending | USER |
| UX-08 | 5 | Onboarding & Config | MÉDIO | Pending | USER |
| UX-09 | 5 | Onboarding & Config | MÉDIO | Pending | USER (onboarding) |
| UI-01 | 6 | UI Visual Redesign | ALTO | Pending | USER (identidade visual) |
| UI-02 | 6 | UI Visual Redesign | ALTO | Pending | USER (layout) |
| UI-03 | 6 | UI Visual Redesign | MÉDIO | Pending | USER (animações) |
| UI-04 | 6 | UI Visual Redesign | MÉDIO | Pending | USER (componentização) |
| PLT-01 | 7 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |
| PLT-02 | 7 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |
| PLT-03 | 7 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |

**Total v1:** 28 requisitos em 7 fases — Coverage: 28/28
