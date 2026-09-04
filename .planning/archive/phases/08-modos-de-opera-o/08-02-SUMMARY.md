---
plan: 08-02
phase: 08-modos-de-opera-o
status: complete
completed_at: 2026-06-27
commit: 47fd183
---

# Plan 08-02 Summary: GeralTab Mode Selector UI Expansion

## What Was Built

Expanded the mode selector in `GeralTab` from 2 buttons (Teste/OBS) to 3 buttons (Teste/Manual/Automático), completing the UI surface for the three-mode system.

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| 1 | Add Manual button, rename OBS→Automático, update tooltips and help | ✓ Done |
| 2 | Rewrite `set_mode()` for 3 canonical values with Teste fallback | ✓ Done |

## Key Files Changed

- `ui/tabs/geral_tab.py` — only file modified

## Key Changes

- **`mode_obs_button` removed** — replaced by `mode_auto_button` (text "Automático")
- **`mode_manual_button` added** — positioned between Teste and Automático
- **`mode_group`** still exclusive, now contains 3 buttons
- **Tooltips** updated for all 3 modes, streamer-oriented language
- **`mode_help_label`** now describes all 3 modes in 3 lines
- **`set_mode()`** maps `"automatico"` → `mode_auto_button`, `"manual"` → `mode_manual_button`, anything else (including `"teste"`) → `mode_test_button` (safe fallback)

## Contract for Plan 03

Plan 03 (`main_window.py`) must wire to these attributes:
- `mode_test_button`, `mode_manual_button`, `mode_auto_button`
- `mode_obs_button` no longer exists — any reference to it in main_window will break

## Verification

- `geral-widgets-ok` — 3 buttons, exclusive group, no mode_obs_button, correct texts
- `set-mode-ok` — all 3 canonical values + fallback route correctly
- `parse-ok` — AST parse clean

## Self-Check: PASSED
