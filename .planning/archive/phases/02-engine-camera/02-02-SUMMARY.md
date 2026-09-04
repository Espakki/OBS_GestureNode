---
phase: 02-engine-camera
plan: "02"
subsystem: gesture-engine
status: complete
tags: [stabilization, detection, false-positives, ENG-02, config]
requires: []
provides:
  - engine/gesture_engine.py::GestureEngine._setup (detection_window_size=7, detection_min_hits=5)
  - config.json::gestures.detection_window_size
  - config.json::gestures.detection_min_hits
affects: [engine/gesture_engine.py, config.json]
tech_stack:
  added: []
  patterns: [config-driven defaults, majority-vote stabilization window]
key_files:
  modified:
    - engine/gesture_engine.py
    - config.json
decisions:
  - "detection_window_size=7 / detection_min_hits=5 (71%) — janela de ~233ms a 30fps exige maioria mais forte que 60% anterior"
  - "Chaves persistidas no config.json para ajuste futuro sem recompilar"
metrics:
  duration: "~10 minutos"
  completed: "2026-06-24"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 2
---

# Phase 02 Plan 02: Parâmetros de Estabilização (ENG-02) — Summary

Defaults de estabilização ajustados para `detection_window_size=7` e `detection_min_hits=5` (71% de concordância de frames), reduzindo falsos positivos durante gestos naturais/transitórios sem perda perceptível de responsividade. Chaves persistidas no `config.json` para ajuste futuro.

## Tasks

| Task | Nome | Commit | Status |
|------|------|--------|--------|
| 1 | Ajustar defaults de estabilização em _setup() | 8029223 | Completa |
| 2 | Persistir chaves de estabilização em config.json | 3a9fc88 | Completa |
| 3 | Checkpoint: Validação humana — gesto natural não dispara | — | Aprovado por Winicius (2026-06-24) |

## Changes Made

### engine/gesture_engine.py

**Task 1 — Defaults de estabilização ajustados (8029223):**
- `detection_window_size` default: `5` → `7` (janela de ~233ms a 30fps)
- `detection_min_hits` default: `3` → `5` (exige 71% de concordância, ante 60%)
- `deque(maxlen=max(3, self.detection_window_size))` deriva automaticamente do novo valor — sem alteração necessária
- Config presente continua sobrescrevendo os defaults (comportamento preservado)
- `GestureStabilityMonitor` e parâmetros `motion_pixel_threshold`/`stability_min_frames` não foram tocados

### config.json

**Task 2 — Chaves de estabilização persistidas (3a9fc88):**
- Adicionou `"detection_window_size": 7` na seção `gestures`
- Adicionou `"detection_min_hits": 5` na seção `gestures`
- Posicionadas após `"default_cooldown": 2.0`, antes de `"enable_stability_check"`
- Nenhuma chave existente removida ou alterada
- JSON válido confirmado via `json.load`

## Rationale

Com `window_size=5, min_hits=3` (60%), gestos transitórios durante fala ou aceno podiam atingir o limiar facilmente. Com `window_size=7, min_hits=5` (71%), a janela representa ~233ms a 30fps e exige maioria mais forte — reduz disparos acidentais mantendo responsividade aceitável (+~66ms de latência inicial).

## Threat Mitigations Applied

| Threat ID | Status | Mitigation |
|-----------|--------|-----------|
| T-02-05 | Mitigado | `int(gestures_cfg.get(...))` força conversão — valor não-inteiro no config levanta exceção detectável no startup |
| T-02-04 | Aceito | deque tem maxlen limitado pelo próprio valor; config é arquivo local controlado pelo usuário |

## Checkpoint de Validação Humana

**Task 3 — Validação humana: APROVADO por Winicius (2026-06-24)**

Resultado confirmado:
- Gestos transitórios naturais (aceno, movimentos de fala) NÃO dispararam ações
- Gesto deliberado mantido firme por 2s disparou corretamente
- Responsividade preservada; sem regressão observável

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

## Verification Results

```
Task 1 — verificação AST:
  OK defaults estabilizacao 7/5

Task 2 — verificação JSON:
  OK config.json estabilizacao

Verificação import (venv):
  import OK
  json OK

Greps de aceitação:
  engine/gesture_engine.py:195: detection_window_size", 7
  engine/gesture_engine.py:196: detection_min_hits", 5
  Sem ocorrencia de default 5 (correto)
  Sem ocorrencia de default 3 (correto)
```

## Known Stubs

Nenhum stub presente. As alterações são funcionais e completas.

## Threat Flags

Nenhuma nova superfície de segurança introduzida neste plano.

## Self-Check

- [x] engine/gesture_engine.py modificado e commitado (8029223)
- [x] detection_window_size default = 7 em _setup()
- [x] detection_min_hits default = 5 em _setup()
- [x] Nenhuma referência remanescente a default 5 (window_size) ou default 3 (min_hits)
- [x] config.json modificado e commitado (3a9fc88)
- [x] config.json tem detection_window_size=7 e detection_min_hits=5 na seção gestures
- [x] Chaves existentes (default_hold_time, default_cooldown, bindings, scene_map) preservadas
- [x] import engine.gesture_engine passa no venv
- [x] json.load(config.json) passa sem exceção

## Self-Check: PASSED
