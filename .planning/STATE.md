---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Features & Polish
status: planning
last_updated: "2026-06-27T00:32:00.000Z"
last_activity: 2026-06-27
progress:
  total_phases: 9
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-26)

**Core value:** Um streamer deve conseguir trocar de cena no OBS com um gesto de mão sem tirar as mãos do controle — com detecção confiável e sem configuração técnica.
**Current focus:** Phase 8 — Modos de Operação (não iniciada)

---

## Milestone

**v1.2 "Features & Polish"** — Em andamento

- Baseline: v1.1 (Phases 1–3 completas, Phases 4–7 absorvidas em v1.2)
- Target: v1.2.0

---

## Current Position

Phase: 8 — Modos de Operação
Plan: —
Status: Roadmap criado — aguardando início da Phase 8
Last activity: 2026-06-26 — Roadmap v1.2 criado (9 fases, Phases 8–16)

## Phase Status (v1.1 — histórico)

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Foundation | Completa ✓ | 2026-06-23 |
| 2 | Engine & Camera | Completa ✓ | 2026-06-25 |
| 3 | OBS Connection | Completa ✓ | 2026-06-25 |
| 4 | Preview UX | Absorvida → Phase 12 (v1.2) | — |
| 5 | Onboarding & Config | Absorvida → Phase 14 (v1.2) | — |
| 6 | UI Visual Redesign | Absorvida → Phase 15 (v1.2) | — |
| 7 | Platform Abstraction | Absorvida → Phase 16 (v1.2) | — |

## Phase Status (v1.2 — ativo)

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 8 | Modos de Operação | Not started | - |
| 9 | HandTracker API Refactor | Not started | - |
| 10 | Config Schema + Detection Engine | Not started | - |
| 11 | Combined Gesture UI + Presets | Not started | - |
| 12 | Preview Overlay | Not started | - |
| 13 | Camera Settings | Not started | - |
| 14 | Onboarding & Config UX | Not started | - |
| 15 | UI Visual Redesign | Not started | - |
| 16 | Platform Abstraction | Not started | - |

---

## Performance Metrics

| Metric | Baseline (v1.1) | Target (v1.2.0) |
|--------|-----------------|-----------------|
| FPS sustentado — 1 mão | 28-35 FPS ✓ | manter 28-35 FPS |
| FPS sustentado — 2 mãos | não medido | 20-28 FPS (model_complexity=0 obrigatório) |
| Latência de captura (C920 MJPEG) | ~42-52ms (medido) → **0ms lag** ✓ spike 619926a | eliminado via PyAV + GPU decode; manter em 1080p 30fps |
| Config corruption risk | zero (debounce 500ms + atomic write) ✓ | manter |
| Config migration (v1.1 → v1.2) | — | silenciosa, sem perda de bindings existentes |

---

## Accumulated Context

### Key Decisions

| Decision | Phase | Rationale |
|----------|-------|-----------|
| Adiar Linux para v2.0 | All | Abstrair código bagunçado é retrabalho duplo; corrigir primeiro, abstrair depois |
| Platform abstraction em Phase 16 | 16 | Sempre última — maior superfície de merge conflict |
| Manter MediaPipe 0.10.14 | 9+ | Tasks API é breaking change radical; sem ganho dentro do 0.10.x |
| Loop único captura+MediaPipe | 2 | GIL torna producer-consumer marginal; gargalo é MediaPipe, não I/O |
| Winicius faz commits/tags manualmente | All | Preferência explícita; Claude instrui, usuário executa |
| GESTURE_ALIASES como módulo de dados puro | 1 (01-03) | Zero imports/funções evita dependência circular; identidade de objeto preservada |
| threading.RLock (não Lock) para bindings | 1 (01-04) | _normalize_gesture_keys() reentra o lock; RLock evita deadlock |
| Config path via __file__ + debounce/atomic save | 1 (01-05) | Path independe do CWD; debounce 500ms + tmp/os.replace elimina corrupção |
| CAP_MSMF excluído de v1.2 | 13 | 80+ segundos de init em câmeras MJPEG — não viável |
| Virtual cam relay excluído de v1.2 | — | blank-frame bug no OpenCV (issue #19746) + sem benefício de lag |
| PyAV (FFmpeg/DirectShow) como backend de captura | 13 | Spike 619926a confirmou: GPU decode MJPEG via dxva2, lag eliminado em 1080p, OpenCV descartado para captura |
| Modo "automático" como padrão de fábrica | 8 | UX objetivo: abre, configura gestos, aperta iniciar — zero fricção técnica para o usuário |
| Configurações de câmera → painel "Avançado" oculto | 14 | PyAV elimina necessidade de expor tipo de captura; só power users precisam das opções avançadas |
| Preview suprimida ao minimizar (modo OBS ativo) | 15 | Evita render duplo: UI + pyvirtualcam → CPU desnecessária quando janela não está visível |
| commit atômico Phase 9 | 9 | hand_tracker.py + gesture_engine.py inseparáveis — API quebra engine se atualizados independentemente |

### Phase Dependencies (v1.2 Critical Order)

```
Phase 8 (modos)     → independente, impacta UI existente
Phase 9 (HandTracker API) → CRÍTICO: prerequisite para Phases 10, 11, 12
Phase 10 (schema + engine) → depende Phase 9; prerequisite para Phase 11
Phase 11 (combined UI) → depende Phase 10
Phase 12 (preview overlay) → depende Phase 9 (per-hand data para 2 barras)
Phase 13 (camera settings) → independente das Phases 9-12; evitar changes concurrent em camera.py
Phase 14 (onboarding) → depende Phases 11, 12
Phase 15 (UI redesign) → depende Phase 14
Phase 16 (platform abstraction) → sempre última
```

### Known Technical Risks

- `GestureStabilityMonitor` colapsa em mudança de contagem de mãos — uma instância por mão, nunca lista merged (Phase 9)
- Handedness invertido em frames pré-espelhados — MediaPipe "Right" = mão física esquerda quando flip já aplicado (Phase 9, smoke test obrigatório)
- Config migration silenciosa — todos os novos campos devem usar `.get(key, default)` (Phase 10)
- FPS real em modo 2 mãos em hardware low-end — estimar na Phase 9, documentar na aba Geral se < 20 FPS

### Todos

- [ ] Rodar Phase 8 — verificar modos no UI antes de iniciar track 2 mãos
- [ ] Smoke test obrigatório na Phase 9: levantar mão direita → confirmar label "Right" no preview
- [ ] Validar FPS em modo 2 mãos durante Phase 9 (estimativa: 20-28 FPS)
- [ ] Testar carregamento de config.json v1.1 sem exceção na Phase 10
- [ ] Verificar formato canônico da chave em combined gesture na Phase 11 ("OPEN_PALM+OPEN_PALM", não nome de display)

### Pending Captured Todos

- [x] Investigar lag em resoluções altas — **resolvido** spike 619926a (PyAV)
- [x] Low-latency capture via backend alternativo — **resolvido** spike 619926a (PyAV)
- [ ] [Detectar 2 mãos e gestos combinados](.planning/todos/pending/2026-06-26-deteccao-de-2-maos-e-gestos-combinados.md) — Phases 9-11
- [ ] [Modo automático como padrão de fábrica](.planning/todos/pending/2026-06-27-modo-automatico-como-padrao-de-fabrica.md) — Phase 8
- [ ] [Configurações de câmera → Configurações Avançadas oculto](.planning/todos/pending/2026-06-27-configuracoes-de-camera-vira-configuracoes-avancadas.md) — Phase 14
- [ ] [OBS Virtual Cam — modos automático e manual](.planning/todos/pending/2026-06-27-obs-virtual-cam-modo-automatico-e-manual.md) — Phase 13
- [ ] [Suprimir preview ao minimizar (modo OBS ativo)](.planning/todos/pending/2026-06-27-suprimir-preview-ao-minimizar-em-modo-obs.md) — Phase 15

---

## Workflow Preferences

- Mode: interactive
- Granularity: fine
- Parallelization: true
- Research: enabled
- Plan Check: enabled
- Verifier: enabled
- Git: Winicius faz commits e tags manualmente

---

## Session Continuity

**Stopped at:** Spike PyAV confirmado + escopo v1.2 atualizado
**Resume file:** None

**Last session:** 2026-06-27
**Next action:** Iniciar Phase 8 — `/gsd-plan-phase 8`
**Context files:**

- `.planning/PROJECT.md` — core value, constraints, decisions
- `.planning/REQUIREMENTS.md` — 27 requisitos ativos v1.2 com traceability completa
- `.planning/ROADMAP.md` — v1.1 (completa) + v1.2 (9 fases, Phases 8–16)
- `.planning/research/SUMMARY.md` — pitfalls críticos e recomendações de arquitetura v1.2
- `.planning/codebase/` — mapa completo da codebase existente (ARCHITECTURE, CONCERNS, STACK, etc.)

---

*Last updated: 2026-06-26 — milestone v1.2 "Features & Polish" roadmap criado*

## Decisions

- [Phase 1]: 02-01: CAM-04 shutdown
- [Phase 1]: 02-01: encerrar resiliente
- [Phase 1]: 02-01: logger
- [Phase 2]: detection_window_size=7 e detection_min_hits=5 (71%) reduzem falsos positivos em ENG-02
- [Phase 3]: obs_footer_label em QHBoxLayout status_row com addStretch (03-02)
