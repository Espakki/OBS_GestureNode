# Requirements — OBS GestureNode v1.2 "Features & Polish"

**Versão:** v1.2.0
**Baseline:** v1.1 (Phases 1–3 completas: Foundation, Engine & Camera, OBS Connection)
**Escopo:** Novos modos de operação, detecção de 2 mãos com gestos combinados, configurações avançadas de câmera, e UX/UI polish completo

---

## v1 Requirements

### Categoria: Modos de Operação (novo)

Sistema de 3 modos que controla exclusivamente como a integração WebSocket/VCam funciona.
O modo NÃO afeta as configurações de câmera (separação explícita).

- [ ] **MODE-01**: Modo **Teste** (existente, renomear/preservar) — sem conexão WebSocket, sem VCam output. Câmera roda e gestos são detectados e exibidos no preview, mas nenhuma ação é executada. Útil para calibrar hold_time e testar gestos sem OBS aberto.
- [ ] **MODE-02**: Modo **Manual** (novo) — WebSocket disponível para conexão manual pelo usuário; VCam output desativado. Ações de atalho de teclado e áudio funcionam normalmente. O usuário pode selecionar OBS Virtual Camera como câmera de entrada sem conflito com output.
- [ ] **MODE-03**: Modo **Automático** (renomear de "OBS") — WebSocket conecta automaticamente ao iniciar; VCam output ativado. Comportamento equivalente ao modo "OBS" atual.
- [ ] **MODE-04**: Seleção de modo é persistida no config.json; padrão é "Teste" na primeira execução para não depender do OBS estar aberto.

### Categoria: Configurações de Câmera (novo)

Configurações de câmera são completamente independentes do modo de operação.

- [ ] **CAM-05**: Câmera tem dois sub-modos: **Padrão do sistema** (configurações de fábrica — câmera negocia o melhor formato disponível automaticamente) e **Personalizado** (usuário configura manualmente).
- [ ] **CAM-06**: No sub-modo Personalizado, UI exibe as opções reais suportadas pelo dispositivo selecionado — enumeradas via DirectShow/pygrabber: resolução, FPS, formato de vídeo (YUY2, MJPEG, etc.) e buffering.
- [ ] **CAM-07**: App mede latência de captura nos primeiros 30 frames e exibe badge passivo (verde/amarelo/vermelho) na aba Geral — sem modal, sem interrupção.
- [ ] **CAM-08**: Se lag medido > 80ms e modo Personalizado disponível, app exibe sugestão proativa inline de trocar para YUY2 em resolução menor. Se lag persistir com todas as opções, sugere selecionar OBS Virtual Camera como câmera de entrada (instrução guiada — sem software adicional necessário).

### Categoria: Detecção de 2 Mãos (novo)

- [ ] **GES-01**: Usuário escolhe modo "1 mão" / "2 mãos" na aba Geral; padrão é "1 mão". Trocar o modo requer restart da engine (não pode ser alterado em tempo real).
- [ ] **GES-02**: No modo "2 mãos", MediaPipe rastreia ambas as mãos simultaneamente (max_num_hands=2, model_complexity=0 obrigatório para manter 20–28 FPS).
- [ ] **GES-03**: Aba Gestos exibe seção "Gestos Combinados (2 mãos)" quando modo "2 mãos" está ativo — oculta quando modo "1 mão" está ativo.
- [ ] **GES-04**: Seção de gestos combinados inclui 6 presets pré-definidos para streamers: Go Live (🖐+🖐), Encerrar (✊+✊), BRB (✊+🖐), Celebrar (👍+👍), Gravar (✊+👍), Câmera Off (🤙+🤙).
- [ ] **GES-05**: Usuário pode criar combinações personalizadas escolhendo gesto da mão esquerda + gesto da mão direita via dialog de configuração com preview ao vivo dos gestos detectados.
- [ ] **GES-06**: Gesto combinado dispara quando AMBAS as mãos mantêm o gesto pelo hold_time completo — cooldown e hold_time se aplicam ao par como unidade.
- [ ] **GES-07**: config.json v2 com campos `max_maos` (padrão: 1), `combined_bindings` (lista de {left, right, action}), e `config_version: 2`. Arquivos v1.1 sem esses campos carregam com defaults silenciosos — sem exceção, sem perda de configuração existente.

### Categoria: Preview e Feedback Visual (v1.1 pendente)

- [ ] **UX-05**: Preview da câmera exibe overlay com nome do gesto detectado atualmente — desenhado diretamente no frame OpenCV. Em modo 2 mãos, exibe labels "Esquerda: [Gesto]" e "Direita: [Gesto]" posicionados espacialmente.
- [ ] **UX-06**: Preview exibe barra de progresso de hold time crescendo enquanto o gesto é mantido; flash visual confirma o disparo da ação. Em modo 2 mãos, exibe duas barras de progresso independentes.

### Categoria: Configuração e UX (v1.1 pendente)

- [ ] **UX-07**: Fluxo de configurar gesto → ação é intuitivo: ao abrir o dialog de configuração de um gesto, o preview exibe qual gesto está sendo detectado em tempo real.
- [ ] **UX-08**: Campos de configuração com validação inline: arquivo .wav exibe erro "Arquivo não encontrado" ao sair do campo com caminho inválido; hotkey exibe combinação capturada em tempo real enquanto o usuário pressiona teclas.
- [ ] **UX-09**: Dialog de primeira execução (first_run: true no config) com checklist de 4 passos: (1) verificar câmera, (2) selecionar modo de operação, (3) conectar OBS se necessário, (4) configurar primeiro gesto.

### Categoria: UI Visual Redesign (v1.1 pendente)

- [ ] **UI-01**: Identidade visual consistente — paleta de cores definida, tipografia uniforme, tema dark mode como padrão (adequado para streamers em ambiente de studio).
- [ ] **UI-02**: Layout e espaçamento revisados — proporções de abas balanceadas, alinhamento em grid consistente, hierarquia visual clara entre seções.
- [ ] **UI-03**: Hover states e transições suaves em todos os controles interativos — botões, sliders, toggles, indicadores de status.
- [ ] **UI-04**: Componentização — widgets reutilizáveis para cards de configuração de gesto; seção de gestos combinados integrada visualmente à aba de gestos existente.

### Categoria: Platform Abstraction (v1.1 pendente)

- [ ] **PLT-01**: Módulo `platform/` com `_protocol.py` (interfaces AudioBackend, InputBackend, CameraEnumerator) e `_windows.py` (implementações atuais isoladas).
- [ ] **PLT-02**: Todo código platform-específico (winsound, ctypes, cv2.CAP_DSHOW, pygrabber) movido para `platform/_windows.py` — nenhum import direto fora do módulo de plataforma.
- [ ] **PLT-03**: ActionManager recebe AudioBackend e InputBackend por injeção de dependência — sem acoplamento direto a implementações Windows.

---

## Validated (v1.1 — completos, não reabrir)

- ✓ **ENG-03**: GESTURE_ALIASES consolidado em core/gesture_aliases.py — Phase 1
- ✓ **ENG-04**: gesture_bindings/mapa_cenas protegidos por threading.RLock — Phase 1
- ✓ **ENG-05**: config.json carregado via __file__ — Phase 1
- ✓ **ENG-06**: salvar_config com debounce 500ms + write atômico — Phase 1
- ✓ **DEP-01**: pygrabber adicionado ao requirements.txt — Phase 1
- ✓ **DEP-02**: Dependências com versões fixadas — Phase 1
- ✓ **CAM-01**: Resize 640×480 antes do MediaPipe — Phase 2
- ✓ **CAM-02**: model_complexity=0, min_tracking_confidence=0.5 — Phase 2
- ✓ **CAM-03**: process_fps cap no loop da engine — Phase 2
- ✓ **CAM-04**: shutdown limpo sem "câmera ocupada" — Phase 2
- ✓ **ENG-01**: hold_time configurável mínimo 0.5s — Phase 2
- ✓ **ENG-02**: detection_window_size=7, min_hits=5 — Phase 2
- ✓ **UX-04**: Conexão OBS em QThread separado — Phase 3
- ✓ **OBS-01**: Handshake get_version() antes de setar connected=True — Phase 3
- ✓ **UX-02**: Indicador de status OBS sempre visível — Phase 3
- ✓ **UX-03**: Mensagens de erro OBS classificadas e acionáveis — Phase 3

---

## v2 Requirements (Deferred)

- Suporte Linux com paridade total (sounddevice, pynput, v4l2loopback)
- Reconexão automática ao OBS após queda de conexão
- Gestos temporais (sequência: gesto A então gesto B)
- Por-mão hold_time independente
- Auto-update do aplicativo
- Cloud sync de configurações

---

## Out of Scope (v1.2 e além)

- CAP_MSMF como backend (80+ segundos de init em câmeras MJPEG — não viável)
- Loop interno pyvirtualcam como câmera de entrada (blank-frame bug no OpenCV + sem benefício de lag)
- Unity Capture ou qualquer software de câmera virtual externo como dependência
- Gestos de 1 mão adicionais além dos 8 existentes
- Plugin system / extensibilidade por terceiros
- Multi-câmera simultânea

---

## Traceability

| REQ-ID | Phase | Phase Name | Prioridade | Status | Fonte |
|--------|-------|------------|------------|--------|-------|
| MODE-01 | 8 | Modos de Operação | ALTO | Pending | USER (keep teste) |
| MODE-02 | 8 | Modos de Operação | ALTO | Pending | USER (modo Manual) |
| MODE-03 | 8 | Modos de Operação | ALTO | Pending | USER (rename OBS→Automático) |
| MODE-04 | 8 | Modos de Operação | MÉDIO | Pending | UX best practice |
| GES-01 | 9 | HandTracker API Refactor | CRÍTICO | Pending | ARCHITECTURE.md + PITFALLS.md |
| GES-02 | 9 | HandTracker API Refactor | CRÍTICO | Pending | STACK.md (max_num_hands=2) |
| GES-06 | 10 | Config Schema + Detection Engine | ALTO | Pending | STACK.md (combined gesture state) |
| GES-07 | 10 | Config Schema + Detection Engine | CRÍTICO | Pending | PITFALLS.md (config migration) |
| GES-03 | 11 | Combined Gesture UI | ALTO | Pending | USER + FEATURES.md |
| GES-04 | 11 | Combined Gesture UI | MÉDIO | Pending | FEATURES.md (6 presets) |
| GES-05 | 11 | Combined Gesture UI | ALTO | Pending | USER (configurações personalizadas) |
| UX-05 | 12 | Preview Overlay | ALTO | Pending | USER + FEATURES.md |
| UX-06 | 12 | Preview Overlay | ALTO | Pending | FEATURES.md (hold progress bar) |
| CAM-05 | 13 | Camera Settings | ALTO | Pending | USER (sub-modos câmera) |
| CAM-06 | 13 | Camera Settings | ALTO | Pending | USER (enumeração de formatos) |
| CAM-07 | 13 | Camera Settings | MÉDIO | Pending | STACK.md (latency measurement) |
| CAM-08 | 13 | Camera Settings | MÉDIO | Pending | USER (sugestão guiada) |
| UX-07 | 14 | Onboarding & Config UX | MÉDIO | Pending | USER |
| UX-08 | 14 | Onboarding & Config UX | MÉDIO | Pending | USER |
| UX-09 | 14 | Onboarding & Config UX | MÉDIO | Pending | USER (onboarding) |
| UI-01 | 15 | UI Visual Redesign | ALTO | Pending | USER (identidade visual) |
| UI-02 | 15 | UI Visual Redesign | ALTO | Pending | USER (layout) |
| UI-03 | 15 | UI Visual Redesign | MÉDIO | Pending | USER (animações) |
| UI-04 | 15 | UI Visual Redesign | MÉDIO | Pending | USER (componentização) |
| PLT-01 | 16 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |
| PLT-02 | 16 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |
| PLT-03 | 16 | Platform Abstraction | MÉDIO | Pending | ARCHITECTURE.md |

**Total v1.2 ativos:** 27 requisitos em 9 fases (Phases 8–16)
**Total validados (v1.1):** 16 requisitos — completos

---

*Last updated: 2026-06-26 — milestone v1.2 "Features & Polish"*
