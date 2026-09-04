---
phase: 02-engine-camera
plan: "05"
subsystem: engine
tags: [fps-cap, process-fps, time-based-sleep, cadence-control]
dependency_graph:
  requires: ["02-01", "02-03"]
  provides: ["CAM-03"]
  affects: ["engine/gesture_engine.py", "config.json", "ui/main_window.py"]
tech_stack:
  added: []
  patterns: ["time-based FPS cap", "time.monotonic() loop timing"]
key_files:
  created: []
  modified:
    - engine/gesture_engine.py
    - config.json
    - ui/main_window.py
decisions:
  - "Posicionamento de _loop_start como primeira instrução do while (antes do try interno) garante que elapsed inclua tanto o processamento de frame quanto qualquer overhead de controle de fluxo"
  - "Guard max(1, process_fps) protege contra divisão por zero quando process_fps=0 ou valor negativo em config"
  - "sleep apenas quando sleep_time > 0 — sem acúmulo de atraso quando MediaPipe demora mais que o intervalo"
  - "time.sleep(0.01) do caminho de falha ler_frame preservado sem alteração"
metrics:
  duration_minutes: 20
  completed_date: "2026-06-24"
  tasks_completed: 3
  tasks_total: 3
status: complete
requirements: [CAM-03]
---

# Phase 02 Plan 05: FPS Cap Time-Based no Loop da Engine — Summary

**One-liner:** FPS cap configurável via `process_fps` com `time.monotonic()` sleep time-based no loop da engine, desacoplando inferência da captura.

## Objective Achieved

CAM-03 satisfeito. Teto de FPS de processamento configurável via `camera.process_fps` implementado e validado pelo usuário em condições reais (480p, ~30fps). Cadência estável confirmada.

## Tasks Completed

### Task 1: FPS cap time-based no loop da engine
**Commit:** `ebc9aef`
**Files:** `engine/gesture_engine.py`

Adicionado em `GestureEngine._setup()`:
- `self.process_fps = int(camera_cfg.get("process_fps", 30))` — lê da seção `camera` do config
- `self._frame_interval = 1.0 / max(1, self.process_fps)` — guard contra divisão por zero

Adicionado em `GestureEngine.run()`:
- `_loop_start = time.monotonic()` — primeira instrução do `while self.running:` (antes do `try:` interno)
- Sleep time-based após `frame_ready.emit(frame)`: `elapsed = time.monotonic() - _loop_start; sleep_time = self._frame_interval - elapsed; if sleep_time > 0: time.sleep(sleep_time)`
- `time.sleep(0.01)` do caminho `if not ok` preservado sem alteração

### Task 2: Persistir process_fps em config.json e schema do main_window
**Commit:** `4a54a6a`
**Files:** `config.json`, `ui/main_window.py`

- `config.json`: adicionado `"process_fps": 30` na seção `camera` após `"fps": 30` — JSON válido, todas as chaves existentes preservadas
- `ui/main_window._init_config_schema()`: adicionado `camera_cfg.setdefault("process_fps", 30)` após `camera_cfg.setdefault("fps", 30)`

### Task 3: Checkpoint — Validação Humana
**Status:** APROVADO pelo usuário em 2026-06-24

Resultado observado pelo usuário: cadência estável em 480p a ~30fps funcional. CAM-03 satisfeito.

## Verification Results

Verificações automatizadas passaram antes do checkpoint:

```
OK FPS cap engine          — process_fps/_frame_interval em _setup(); time.monotonic()+sleep em run()
OK process_fps config+schema — config.json parseia; camera.process_fps==30; setdefault em main_window
syntax OK engine           — ast.parse sem SyntaxError
syntax OK main_window      — ast.parse sem SyntaxError
json OK config             — json.load sem erro
```

Validacao humana: usuario confirmou cadencia estavel em 480p a ~30fps. FPS cap funcional.

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

## Deferred Items

**Bug observado durante checkpoint (fora do escopo deste plano):**

O usuario reportou que as opcoes de resolucao afetam a imagem deixando-a "espremida" (aspect ratio incorreto no preview widget Qt). Este bug e proveniente do Plan 02-03 (HandTracker retorna frames sempre em 640x480 independente da resolucao selecionada; o widget Qt nao preserva aspect ratio). Nao e regressao introduzida pelo 02-05.

Registrado para fix posterior: o `preview_label` em `ui/main_window.py` usa `Qt.KeepAspectRatio` no `.scaled()` mas o frame emitido pelo HandTracker pode ter dimensoes fixas que divergem do tamanho do widget, causando distorcao visual quando o usuario seleciona resolucoes diferentes de 480p.

## Threat Surface Scan

Mitigacoes do threat model implementadas:
- **T-02-10** (DoS / divisao por zero): `max(1, self.process_fps)` implementado — processo nao crasha com `process_fps=0`
- **T-02-11** (DoS / CPU 100%): aceito por design — comportamento equivalente ao estado pre-fase quando `process_fps` muito alto

## Known Stubs

Nenhum — implementacao completa sem placeholders.

## Self-Check: PASSED

- [x] `engine/gesture_engine.py` modificado com `process_fps`, `_frame_interval`, `_loop_start`, sleep time-based
- [x] `config.json` modificado com `camera.process_fps = 30` (JSON valido)
- [x] `ui/main_window.py` modificado com `setdefault("process_fps", 30)`
- [x] Commit `ebc9aef` existe: `feat(02-05): FPS cap time-based no loop da engine`
- [x] Commit `4a54a6a` existe: `feat(02-05): persistir process_fps em config.json e schema do main_window`
- [x] Checkpoint humano aprovado: cadencia estavel em 480p confirmada pelo usuario
