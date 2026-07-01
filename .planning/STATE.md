---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: milestone
current_phase: 04
current_phase_name: preview-ux
status: planning
stopped_at: Phase 03 complete — UAT passed (8/9, 1 fix applied)
last_updated: "2026-06-25T23:03:00.000Z"
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 13
  completed_plans: 13
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-22)

**Core value:** Um streamer deve conseguir trocar de cena no OBS com um gesto de mão sem tirar as mãos do controle — com detecção confiável e sem configuração técnica.
**Current focus:** Phase 04 — preview-ux

---

## Milestone

**v1.1 "Stability & Polish"** — Em andamento

- Baseline: v1.0.0 (taggeada)
- Target: v1.1.0

---

## Current Position

**Phase:** 04 (preview-ux) — PLANNING
**Plan:** 0 of ?
**Status:** Ready to plan
**Progress:** [----------] 0%

```
[Phase 1] [Phase 2] [Phase 3] [Phase 4] [Phase 5] [Phase 6] [Phase 7]
   ✓          ✓          ✓          ○          ○          ○          ○
```

---

## Phase Status

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Foundation | Completa ✓ | 2026-06-23 |
| 2 | Engine & Camera | Not started | - |
| 3 | OBS Connection | Not started | - |
| 4 | Preview UX | Not started | - |
| 5 | Onboarding & Config | Not started | - |
| 6 | UI Visual Redesign | Not started | - |
| 7 | Platform Abstraction | Not started | - |

---

## Performance Metrics

| Metric | Baseline (v1.0.0) | Target (v1.1.0) |
|--------|-------------------|-----------------|
| FPS sustentado (CPU mid-range) | ~15-20 FPS | ~28-35 FPS |
| Falsos positivos | não medido | reduzido com detection_min_hits=5/7 |
| Hold time padrão | 2.0s (fixo) | 2.0s (ajustável, mínimo 0.5s) |
| Config corruption risk | alta (sem debounce) | zero (debounce 500ms + atomic write) ✓ ENG-06 |
| Installs quebrados | pygrabber ausente | todas deps fixadas no requirements.txt ✓ DEP-01/02 |

---
| Phase 02 P01 | 15m | 2 tasks | 1 files |
| Phase 02 P01 | 15m | 3 tasks | 1 files |
| Phase 02 P02 | 10m | 2 tasks | 2 files |
| Phase 03 P02 | 10min | 2 tasks | 1 files |
| Phase 03 P03 | 5min | 1 tasks | 1 files |

## Accumulated Context

### Key Decisions

| Decision | Phase | Rationale |
|----------|-------|-----------|
| Adiar Linux para v2.0 | All | Abstrair código bagunçado é retrabalho duplo; corrigir primeiro, abstrair depois |
| Platform abstraction em Phase 7 | 7 | Feita por último — todas as correções e features devem estar estáveis antes |
| Manter MediaPipe 0.10.14 | 2 | Tasks API é breaking change radical; sem ganho dentro do 0.10.x |
| Loop único captura+MediaPipe | 2 | GIL torna producer-consumer marginal; gargalo é MediaPipe, não I/O |
| Winicius faz commits/tags manualmente | All | Preferência explícita; Claude instrui, usuário executa |
| GESTURE_ALIASES como módulo de dados puro | 1 (01-03) | Zero imports/funções evita dependência circular; identidade de objeto preservada |
| threading.RLock (não Lock) para bindings | 1 (01-04) | _normalize_gesture_keys() reentra o lock; RLock evita deadlock. Getter sem cópia defensiva preserva mutação in-place |
| Config path via __file__ + debounce/atomic save | 1 (01-05) | Path independe do CWD (não cria config em system32); debounce 500ms + tmp/os.replace elimina corrupção e .tmp órfãos |

### Phase Dependencies (Critical Order)

```
ENG-05 (fix config path)  →  ENG-06 (debounce save)        ✓ ambos done (01-05)
ENG-04 (threading lock)   →  ENG-01 (engine stability)     ✓ ENG-04 done (01-04)
ENG-03 (GESTURE_ALIASES)  →  UX-05/06 (overlay nome gesto) ✓ ENG-03 done (01-03)
UX-04 (non-blocking OBS)  →  UX-02 (status) + UX-03 (erros)
CAM-01 (decouple res)     →  CAM-02 (seletor de resolução)
Phase 1-5                 →  Phase 7 (platform abstraction)
```

### Known Technical Risks

- `obsws-python` behavior during mid-session disconnection — testar empiricamente na Phase 3
- FPS real em hardware low-end de streamer — verificar estimativas na Phase 2
- Wayland input simulation em distros Linux — endereçar no planejamento da Phase 7

### Todos

- [ ] Rodar verificação formal da Phase 1 (gsd-verifier) antes de iniciar a Phase 2
- [ ] Validar estimativas de FPS (28-35) em hardware real durante Phase 2
- [ ] Testar comportamento de `obsws-python` em desconexão inesperada durante Phase 3
- [ ] Pesquisa adicional sobre pynput + v4l2loopback antes de iniciar Phase 7

### Pending Captured Todos (1)

- [ ] [Investigar lag em resoluções altas com MediaPipe e webcams](.planning/todos/pending/2026-06-25-investigar-lag-em-resolu-es-altas-com-mediapipe-e-webcams.md) — engine · lag 720p/1080p · crítico para escopo

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

**Stopped at:** Completed 03-02-PLAN.md
**Resume file:** None

**Last session:** 2026-06-25T21:54:09.621Z
**Next action:** Executar planos restantes da Phase 2 (02-03, 02-04, 02-05) — Wave 2 e Wave 3
**Context files:**

- `.planning/PROJECT.md` — core value, constraints, decisions
- `.planning/REQUIREMENTS.md` — requisitos com traceability
- `.planning/ROADMAP.md` — 7 fases com success criteria
- `.planning/research/SUMMARY.md` — pitfalls críticos e recomendações de arquitetura
- `.planning/codebase/` — mapa completo da codebase existente (ARCHITECTURE, CONCERNS, STACK, etc.)

---

*Last updated: 2026-06-23*

## Decisions

- [Phase ?]: 02-01
- [Phase ?]: 02-01: CAM-04 shutdown
- [Phase ?]: 02-01: encerrar resiliente
- [Phase ?]: 02-01: logger
- [Phase ?]: detection_window_size=7 e detection_min_hits=5 (71%) reduzem falsos positivos em ENG-02
- [Phase ?]: obs_footer_label em QHBoxLayout status_row com addStretch (03-02)
