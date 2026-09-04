---
phase: 01-foundation
plan: 02
subsystem: config
tags: [config.json, fresh-install, template, cleanup]

# Dependency graph
requires: []
provides:
  - "config.json limpo sem dados do developer — template de fresh install"
  - "camera.index=0 (câmera padrão), obs.host=localhost, todos os bindings vazios"
affects:
  - 01-03
  - 01-04
  - 01-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "config.json commitado como template de estado fresh-install sem dados de ambiente do developer"

key-files:
  created: []
  modified:
    - config.json

key-decisions:
  - "D-01: config.json limpo commitado — estrutura correta, sem paths absolutos ou placeholders"
  - "D-02: Todos os bindings vazios — sem ações pré-configuradas, consistente com comportamento do .exe"
  - "Caracteres unicode (Mão aberta, Três) escritos literalmente no JSON em vez de escape \\uXXXX — mais legível para manutenção manual"

patterns-established:
  - "config.json no repo representa fresh install: index=0, host=localhost, bindings todos vazios"

requirements-completed: [ENG-05, ENG-06]

# Metrics
duration: 5min
completed: 2026-06-22
status: complete
---

# Phase 1 Plan 02: Config Template Summary

**config.json reescrito como template de fresh install: camera.index=0, obs.host=localhost, 14 gestos com bindings vazios, scene_map={}, sem path absoluto/IP de rede/placeholder de hotkey do developer**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-22T21:33:00-03:00
- **Completed:** 2026-06-22T21:38:00-03:00
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Removido path absoluto `D:/Documentos/Codes/gesto_camera/faz-o-l.wav` do gesto "V" (T-02-01 mitigado)
- Removido IP de rede do developer `192.168.1.3` do obs.host — substituído por `localhost` (T-02-02 mitigado)
- Removido placeholder `"Pressione as teclas..."` do gesto "Escoteiro" com `use_hotkey=false` (T-02-03 mitigado)
- Todos os 14 gestos agora têm `scene=""`, `sound_file=""`, `hotkey=""`, `use_scene=false`, `use_sound=false`, `use_hotkey=false`
- `scene_map` esvaziado para `{}`, `camera.index` corrigido de 1 para 0, `camera.device_name` para `""`

## Task Commits

1. **Task 1: Reescrever config.json como template limpo de fresh install** - `03b4f0f` (feat)

## Files Created/Modified

- `config.json` — reescrito como template de fresh install (220 linhas → estrutura idêntica, dados do developer removidos)

## Decisions Made

- Caracteres unicode (`Mão aberta`, `Três`) escritos literalmente no JSON (UTF-8), não como sequências `\uXXXX` — o arquivo original usava escape em `â` mas o app usa `json.dump(ensure_ascii=False)` no salvamento; consistência com o comportamento de save do app.
- `active_gestures` mantido com os 11 gestos ativos do original (Rock, Três, Quatro foram omitidos da lista de ativos pois estão `enabled: false` — comportamento original preservado).

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

## Issues Encountered

Nenhum.

## User Setup Required

Nenhum — apenas arquivo de dados reescrito, sem serviços externos, sem variáveis de ambiente.

## Next Phase Readiness

- `config.json` limpo disponível para os planos 01-03 (ENG-05: config path) e 01-04 (ENG-06: atomic save) operarem sobre dados corretos desde o início
- Qualquer clone do repositório agora parte de um estado fresh sem herdar configuração quebrada do developer

## Self-Check

- [x] `config.json` existe em `D:\Documentos\Codes\OBS_GestureNode\config.json`
- [x] `json.load(open('config.json', encoding='utf-8'))` retorna sem exceção
- [x] `gesto_camera` ausente do arquivo
- [x] `Pressione as teclas` ausente do arquivo
- [x] `192.168.1.3` ausente do arquivo
- [x] `"index": 0` presente
- [x] Todos os bindings com `use_scene=false`, `use_sound=false`, `use_hotkey=false`, `scene=""`, `sound_file=""`, `hotkey=""`
- [x] `scene_map` é `{}`
- [x] Commit `03b4f0f` existe no log do git

## Self-Check: PASSED

---
*Phase: 01-foundation*
*Completed: 2026-06-22*
