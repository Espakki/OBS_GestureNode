# OBS GestureNode

## What This Is

Aplicativo desktop para Windows que permite streamers controlarem o OBS Studio através de gestos de mão detectados pela webcam em tempo real. O usuário configura qual gesto dispara qual ação (trocar de cena, atalho de teclado, reproduzir áudio) e o app faz a detecção via MediaPipe + OpenCV, executando as ações via OBS WebSocket.

## Core Value

Um streamer deve conseguir trocar de cena no OBS com um gesto de mão sem tirar as mãos do controle — com detecção confiável e sem configuração técnica.

## Current Milestone: v1.2 "Features & Polish"

**Goal:** Adicionar low-latency capture nativa, detecção de 2 mãos com gestos combinados configuráveis, e completar todas as melhorias de UX/UI pendentes da v1.1.

**Target features:**
- [NOVA] Low-latency camera capture — MSMF backend + câmera virtual interna via pyvirtualcam; elimina lag do C920 e similares sem depender de software externo
- [NOVA] Detecção de 2 mãos — MediaPipe max_num_hands=2; aba Gestos ganha seção de gestos combinados configuráveis pelo usuário
- [v1.1] Preview UX — overlay do gesto detectado + barra de progresso de hold time + flash visual ao disparar ação
- [v1.1] Onboarding & Config — wizard primeira execução + validação inline
- [v1.1] UI Visual Redesign — dark theme, paleta consistente, hover states, cards componentizados
- [v1.1] Platform Abstraction — isolar winsound/ctypes/CAP_DSHOW em platform/_windows.py

## Requirements

### Validated

- ✓ Detecção de gestos via webcam usando MediaPipe (mão aberta, punho, polegar para cima/baixo, dedo indicador, paz, mão fechada, L) — existing
- ✓ Integração com OBS via WebSocket 5.x para troca de cenas — existing
- ✓ UI em PySide6 com abas de configuração (Geral, Gestos, OBS) — existing
- ✓ Configuração e captura de atalhos de teclado (hotkeys) por gesto via Win32 SendInput — existing
- ✓ Reprodução de áudio .wav por gesto via winsound — existing
- ✓ Saída de câmera virtual via pyvirtualcam — existing
- ✓ Configuração persistente em config.json com auto-save — existing
- ✓ Preview da câmera com anotações de landmarks no app — existing
- ✓ Dependências fixadas em requirements.txt incluindo pygrabber (DEP-01, DEP-02) — Phase 1
- ✓ GESTURE_ALIASES consolidado em core/gesture_aliases.py (ENG-03) — Phase 1
- ✓ gesture_bindings/mapa_cenas protegidos por threading.RLock (ENG-04) — Phase 1
- ✓ config.json carregado via __file__ + debounce 500ms + write atômico (ENG-05, ENG-06) — Phase 1
- ✓ Pipeline MediaPipe otimizado a 28-35 FPS; câmera encerra sem "câmera ocupada" (CAM-01–04, ENG-01–02) — Phase 2
- ✓ Conexão OBS não-bloqueante + status sempre visível + mensagens de erro acionáveis (UX-02, UX-03, UX-04, OBS-01) — Phase 3

### Active

#### Low-Latency Camera Capture
- [ ] **CAM-05**: App testa cv2.CAP_MSMF como alternativa ao DirectShow; seleciona automaticamente o backend com menor lag
- [ ] **CAM-06**: Se MSMF não resolver lag > threshold, app ativa modo câmera virtual interna (captura física → pyvirtualcam → thread de detecção) de forma transparente ao usuário
- [ ] **CAM-07**: Latência de captura é medida nos primeiros N frames; modo câmera virtual ativa automaticamente sem configuração manual

#### Detecção de 2 Mãos
- [ ] **GES-01**: Usuário pode escolher modo "1 mão" ou "2 mãos" na aba Geral; padrão é "1 mão"
- [ ] **GES-02**: No modo "2 mãos", MediaPipe rastreia ambas as mãos simultaneamente (max_num_hands=2)
- [ ] **GES-03**: Aba Gestos exibe seção de gestos combinados (2 mãos) quando modo "2 mãos" está ativo
- [ ] **GES-04**: Usuário pode criar combinações personalizadas escolhendo gesto da mão esquerda + gesto da mão direita
- [ ] **GES-05**: Cooldown e hold_time se aplicam ao gesto combinado como unidade (não individualmente por mão)
- [ ] **GES-06**: config.json suporta campo `max_maos` e estrutura de bindings para gestos combinados

#### UX e UI — Preview
- [ ] **UX-05**: Preview da câmera exibe o gesto detectado atualmente em destaque visual
- [ ] **UX-06**: Preview exibe barra de progresso de hold time e flash visual ao disparar ação

#### UX e UI — Configuração
- [ ] **UX-07**: Fluxo de configurar gesto → ação é intuitivo e tem feedback visual do gesto sendo detectado enquanto configura
- [ ] **UX-08**: Campos de configuração têm validação e feedback de erro inline (ex: arquivo .wav não encontrado)

#### UX e UI — Onboarding
- [ ] **UX-09**: Usuário novo vê guia de primeiros passos na primeira execução (conectar OBS → testar câmera → configurar primeiro gesto)

#### UI Visual
- [ ] **UI-01**: Todas as abas usam a mesma paleta de cores, tipografia e espaçamento
- [ ] **UI-02**: Dark mode ativo por padrão
- [ ] **UI-03**: Hover states e transições visíveis em todos os controles interativos
- [ ] **UI-04**: Cards de configuração de gesto são componentizados

#### Platform Abstraction
- [ ] **PLT-01**: Nenhum import Windows-específico (winsound, ctypes, CAP_DSHOW, pygrabber) fora de platform/_windows.py
- [ ] **PLT-02**: ActionManager recebe AudioBackend e InputBackend no construtor
- [ ] **PLT-03**: platform/_protocol.py define interfaces; platform/_windows.py contém todas as implementações Windows

### Out of Scope (v1.2)

- Suporte Linux — adiado para v2.0; melhor estruturar bem o Windows antes do port multiplataforma
- Novos gestos de 1 mão — foco em estabilizar os 8 gestos existentes
- Novas combinações de ações (segurar vs. soltar, sequência temporal de gestos) — roadmap futuro
- Autenticação de usuários / cloud sync — app local, sem necessidade
- Mobile / web — fora do escopo do projeto
- Dependência de software externo para câmera virtual (OBS VCam, ManyCam) — solução deve ser nativa

## Context

- **Público-alvo**: streamers que usam OBS Studio no Windows
- **Baseline**: v1.0.0 taggeada com o MVP funcional (câmera → detecção → OBS)
- **Versão corrente**: v1.1 — Phases 1-3 completas (estabilização, engine, OBS connection)
- **Versão alvo**: v1.2.0 "Features & Polish"
- **Versão futura planejada**: v2.0.0 com suporte Linux (port após estrutura consolidada)
- **Codebase mapeada**: `.planning/codebase/` contém análise completa (ARCHITECTURE, CONCERNS, STACK, etc.)
- **Problemas críticos resolvidos na v1.1**: dependências fixadas, GESTURE_ALIASES consolidado, race condition corrigida, OBS não-bloqueante, config path/debounce

### Notas de Arquitetura (v1.2)
- `pyvirtualcam` já está no stack e pode ser reutilizado para loop interno de câmera virtual
- `mediapipe==0.10.14` suporta `max_num_hands=2` nativamente — sem mudança de dependência
- `HandTracker` já retorna lista de landmarks por mão — extensível para 2 mãos
- Thread de captura dedicada já implementada em `core/camera.py` — base para Phase 8

## Constraints

- **Tech Stack**: Python 3.10.11 em venv — manter compatibilidade
- **Plataforma**: Windows exclusivo para v1.2.0; Linux em v2.0.0
- **Dependência crítica**: `mediapipe==0.10.14` pinado — não atualizar sem validar API de landmarks
- **Git workflow**: Winicius faz commits e tags manualmente. Claude fornece os comandos exatos, mas não executa.
- **Sem dependência de software externo**: câmera virtual deve ser resolvida internamente pelo app

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Adiar Linux para v2.0 | Refatorar o código Windows-específico atrás de interfaces de plataforma é muito mais fácil com o código limpo; fazer o port antes da refatoração é retrabalho duplo | — Pending |
| Versionamento semântico (v1.0.0 → v1.1.0 → v2.0.0) | Comunica claramente o escopo de cada versão para usuários e colaboradores | — Pending |
| Feature branches → merge em main; tags em versões lançáveis | Evita branches permanentes por plataforma; mantém histórico limpo | — Pending |
| Desacoplar resolução de captura da resolução de processamento | Permite qualidade visual 1080p + desempenho de MediaPipe a 640p — padrão da indústria | — Pending |
| Winicius gerencia commits/tags manualmente | Preferência explícita de aprendizado de git — Claude instrui, usuário executa | ✓ Definido |

## Evolution

Este documento evolui a cada transição de fase e milestone.

**Após cada transição de fase** (via `/gsd-transition`):
1. Requisitos invalidados? → Mover para Out of Scope com motivo
2. Requisitos validados? → Mover para Validated com referência da fase
3. Novos requisitos emergiram? → Adicionar em Active
4. Decisões a registrar? → Adicionar em Key Decisions
5. "What This Is" ainda está preciso? → Atualizar se derivou

**Após cada milestone** (via `/gsd-complete-milestone`):
1. Revisão completa de todas as seções
2. Core Value check — ainda a prioridade certa?
3. Auditar Out of Scope — motivos ainda válidos?
4. Atualizar Context com estado atual

---
*Last updated: 2026-06-26 — início da milestone v1.2 "Features & Polish"*
