---
plan: 02-04
phase: 02-engine-camera
status: complete
requirement_ids: [ENG-01]
started: 2026-06-24
completed: 2026-06-24
tasks_total: 3
tasks_completed: 3
---

## Summary

`hold_time` agora configurável até 0.5s na UI (era travado em 2.0s). Slider e spinbox aceitam 0.5–5.0s; nota de recomendação visível abaixo do controle; três clamps em `main_window.py` reduzidos de `max(2.0, ...)` para `max(0.5, ...)` para garantir que o valor persiste após salvar/reabrir. Default permanece 2.0s.

## Tasks

| # | Nome | Commit | Status |
|---|------|--------|--------|
| 1 | Range slider/spinbox 0.5s + nota de recomendação | 947a5b2 | ✓ done |
| 2 | Reduzir 3 clamps hold_time para max(0.5) em main_window.py | 8dd6359 | ✓ done |
| 3 | Checkpoint: 0.5s aceito, nota visível, valor persiste | — | ✓ aprovado |

## Key Files

- `ui/tabs/gestos_tab.py` — `hold_slider.setRange(5, 50)`, `hold_value_spinbox.setRange(0.5, 5.0)`, `hold_time_note` QLabel
- `ui/main_window.py` — três clamps `max(2.0)` → `max(0.5)` em `_init_config_schema()` (2×) e `select_gesture()` (1×)

## Deviations

Nenhum. O terceiro clamp (`select_gesture()`) foi aplicado após limite de sessão — commit separado `8dd6359`.

## Self-Check: PASSED

- Slider range (5, 50) ✓
- Spinbox range (0.5, 5.0) ✓
- Nota `hold_time_note` com texto "Recomendado: 2.0s" ✓
- Três clamps `max(0.5, ...)` em main_window.py ✓
- Clamps de cooldown intactos (`max(2.0, ...)`) ✓
- Sem SyntaxError em ambos os arquivos ✓
- Checkpoint humano aprovado por Winicius (2026-06-24) ✓
