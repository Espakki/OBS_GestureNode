---
phase: 08-modos-de-opera-o
plan: "01"
subsystem: engine-actions
status: complete
tags: [modes, action-manager, gesture-engine, vcam, obs-websocket]
completed_date: "2026-06-27"
duration_minutes: 2
tasks_completed: 2
tasks_total: 2
files_changed: 2

dependency_graph:
  requires: []
  provides:
    - ActionManager.modo (string canônica, bloqueia ações em "teste")
    - GestureEngine.modo (normalizado, fonte de verdade de VCam/OBS/bloqueio)
    - Matriz de comportamento por modo totalmente implementada no backend
  affects:
    - engine/gesture_engine.py
    - actions/action_manager.py

tech_stack:
  added: []
  patterns:
    - Guard antecipado em executar() para bloqueio de modo Teste
    - Normalização defensiva de valores canônicos com mapa de migração legado

key_files:
  modified:
    - actions/action_manager.py
    - engine/gesture_engine.py

decisions:
  - "Default de ActionManager é 'automatico' — evita bloqueio silencioso em callers existentes (least surprise)"
  - "Dupla barreira: bloqueio em ActionManager.executar() + guard no loop do engine — defesa em profundidade (D-02)"
  - "enable_virtual_camera derivado exclusivamente de self.modo == 'automatico' — modo é a única fonte de verdade da VCam"
  - "Normalização via _legado_map antes de validar _modos_validos — migração silenciosa v1.1 → v1.2 sem crash"

metrics:
  duration: 2min
  completed_date: "2026-06-27"
---

# Phase 08 Plan 01: Matriz de Modos Backend — Summary

**One-liner:** Guard de modo Teste em ActionManager + normalização canônica e matriz completa (OBS/VCam/ações) no GestureEngine.

---

## What Was Built

Implementação da matriz de comportamento dos três modos no backend, sem tocar na UI:

| Modo       | WebSocket OBS | VCam (pyvirtualcam) | Hotkeys/Áudio |
|------------|---------------|---------------------|---------------|
| teste      | Não conecta   | Desligada           | Bloqueado     |
| manual     | Auto-conecta  | Desligada           | Permitido     |
| automatico | Auto-conecta  | Ligada              | Permitido     |

### Task 1 — ActionManager: bloqueio em modo teste (commit `4e4c989`)

- Assinatura alterada: `__init__(self, obs_controller, modo="automatico")`
- Novo atributo `self.modo = str(modo or "automatico").lower()`
- Guard no início de `executar()`: retorna imediatamente com `logger.info` quando `self.modo == "teste"` — nenhuma chamada a OBS, winsound ou SendInput ocorre

### Task 2 — GestureEngine: matriz completa (commit `ec7f984`)

1. **Normalização de modo** em `_setup()`: lê `config["modo"]`, aplica mapa de migração legado (`"test"` → `"teste"`, `"obs"` → `"automatico"`), valida contra `{"teste","manual","automatico"}`, fallback `"automatico"` — armazena em `self.modo`
2. **VCam por modo**: `CameraManager` recebe `enable_virtual_camera=(self.modo == "automatico")` — modo é a única fonte de verdade
3. **ActionManager com modo**: instanciado com `modo=self.modo` para propagar bloqueio Teste
4. **Conexão OBS por modo**: `_connect_obs()` retorna cedo quando `self.modo not in ("manual", "automatico")` — Teste não conecta OBS
5. **Status passivo Teste**: após "Câmera iniciada", emite `"Modo Teste — ações desativadas"` quando `modo == "teste"` (D-03)
6. **Bloqueio no loop**: guard `self.modo != "teste"` na condição de submissão de ações — defesa em profundidade junto com Task 1

---

## Commits

| Task | Commit    | Descrição                                                  |
|------|-----------|------------------------------------------------------------|
| 1    | `4e4c989` | feat(08-01): bloquear todas as ações da ActionManager em modo teste |
| 2    | `ec7f984` | feat(08-01): aplicar matriz de modo no GestureEngine (OBS, VCam, status) |

---

## Deviations from Plan

None — plano executado exatamente como escrito.

---

## Self-Check: PASSED

- [x] `actions/action_manager.py` existe e compila: `parse-ok`
- [x] `engine/gesture_engine.py` existe e compila: `parse-ok`
- [x] Smoke Task 1: imprimiu `actionmanager-teste-block-ok`
- [x] Smoke Task 2: imprimiu `engine-src-ok`
- [x] Commit `4e4c989` existe
- [x] Commit `ec7f984` existe
- [x] `self.modo` presente nos dois arquivos nos pontos corretos
- [x] `enable_virtual_camera=(self.modo == "automatico")` em gesture_engine.py linha 235
- [x] Guard `_connect_obs()` atualizado para `self.modo not in ("manual", "automatico")`
- [x] Status `"Modo Teste — ações desativadas"` no run() linha 347
- [x] Guard de loop `self.modo != "teste"` linha 405
