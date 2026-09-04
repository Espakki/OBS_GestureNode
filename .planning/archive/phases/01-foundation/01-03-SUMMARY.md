---
phase: 01-foundation
plan: "03"
subsystem: core
tags: [gesture_aliases, refactoring, single-source-of-truth, mediapipe, python]

requires: []
provides:
  - "core/gesture_aliases.py — módulo de dados puro com GESTURE_ALIASES (14 entradas), fonte única de verdade"
  - "gesture_detector.py, gesture_engine.py e main_window.py importam do módulo canônico"
  - "Identidade de objeto garantida: os 3 módulos referenciam o mesmo dict em runtime"
affects:
  - "02-foundation (engine & camera)"
  - "UX-05, UX-06 (overlay com nome do gesto)"

tech-stack:
  added: []
  patterns:
    - "Data-module pattern: módulo Python sem imports e sem funções, apenas constante UPPER_SNAKE_CASE"
    - "Import canônico: from core.gesture_aliases import GESTURE_ALIASES em todos os consumidores"

key-files:
  created:
    - core/gesture_aliases.py
  modified:
    - core/gesture_detector.py
    - engine/gesture_engine.py
    - ui/main_window.py

key-decisions:
  - "GESTURE_ALIASES definido como módulo de dados puro (zero imports, zero funções) — evita dependências circulares e facilita importação por qualquer módulo"
  - "Dict inclui 4 entradas passthrough (V, Escoteiro, Dedo do Meio, Arminha) para cobrir todos os retornos de detectar() sem lookup inconsistente"
  - "Nenhum consumidor faz .copy() do dict — fonte única preservada por identidade de objeto"

patterns-established:
  - "Data-module pattern: constantes compartilhadas vivem em módulo próprio sem dependências"
  - "Union dict: ao consolidar cópias divergentes, incluir todas as chaves + passthrough dos valores que já são display names"

requirements-completed: [ENG-03]

duration: ~30min
completed: "2026-06-22"
status: complete
---

# Phase 01, Plan 03: GESTURE_ALIASES Consolidation Summary

**`GESTURE_ALIASES` movido para `core/gesture_aliases.py` (14 entradas, módulo puro) — 3 cópias divergentes eliminadas, identidade de objeto verificada em runtime pelo usuário**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-06-22
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify)
- **Files modified:** 4

## Accomplishments

- Criado `core/gesture_aliases.py` como fonte única de verdade: dict com 14 entradas (união das 3 cópias divergentes + 4 entradas passthrough cobrindo todos os retornos de `detectar()`)
- Removidas as 3 cópias locais de `GESTURE_ALIASES` de `gesture_detector.py` (atributo de classe), `gesture_engine.py` (constante de módulo) e `main_window.py` (constante de módulo)
- Identidade de objeto confirmada pelo usuário: `e.GESTURE_ALIASES is m.GESTURE_ALIASES is d.GESTURE_ALIASES` → `True`
- `python main.py` inicia sem ImportError; aba de gestos exibe os nomes corretos

## Task Commits

1. **Task 1: Criar core/gesture_aliases.py** — `641971a` (feat)
2. **Task 2: Remover 3 cópias locais e importar do módulo canônico** — `9d1adb2` (refactor)
3. **Task 3: Verificação humana** — aprovada pelo usuário (sem commit de código)

## Files Created/Modified

- `core/gesture_aliases.py` — novo módulo de dados puro; define `GESTURE_ALIASES` com 14 entradas; zero imports, zero funções
- `core/gesture_detector.py` — removido atributo de classe `GESTURE_ALIASES`; adicionado `from core.gesture_aliases import GESTURE_ALIASES` no topo
- `engine/gesture_engine.py` — removida constante de módulo `GESTURE_ALIASES`; adicionado `from core.gesture_aliases import GESTURE_ALIASES` no bloco de imports `from core.*`
- `ui/main_window.py` — removida constante de módulo `GESTURE_ALIASES`; adicionado `from core.gesture_aliases import GESTURE_ALIASES` junto aos imports da engine

## Decisions Made

- **Data-module puro**: o módulo `core/gesture_aliases.py` não importa nada e não define funções — apenas a constante. Isso elimina risco de dependência circular e torna o módulo importável por qualquer consumidor sem efeitos colaterais.
- **4 entradas passthrough incluídas**: `"V" -> "V"`, `"Escoteiro" -> "Escoteiro"`, `"Dedo do Meio" -> "Dedo do Meio"`, `"Arminha" -> "Arminha"`. Sem elas, `GESTURE_ALIASES.get(x, x)` na engine funcionaria por acaso (fallback), mas o dict ficaria semanticamente incompleto — qualquer futuro consumidor que iterasse as chaves não enxergaria esses gestos.
- **Sem `.copy()`**: nenhum consumidor copia o dict, preservando identidade de objeto e garantindo que uma futura modificação centralizada se propague automaticamente.

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado.

## Issues Encountered

Nenhum.

## User Setup Required

Nenhuma — refatoração interna sem dependências externas.

## Next Phase Readiness

- ENG-03 satisfeito: `GESTURE_ALIASES` retorna o mesmo dicionário independente do módulo consultado (Roadmap Success Criterion 5)
- Pré-requisito de `UX-05`/`UX-06` (overlay com nome do gesto) desbloqueado
- Próximos planos da Phase 01 podem importar `from core.gesture_aliases import GESTURE_ALIASES` sem risco de drift

---

## Self-Check: PASSED

- `core/gesture_aliases.py` existe: confirmado (commit 641971a)
- Commits existem: 641971a (Task 1), 9d1adb2 (Task 2) — verificados via git log
- Identidade de objeto: confirmada pelo usuário na Task 3 (checkpoint:human-verify aprovado)
- `python main.py` iniciou sem ImportError: confirmado pelo usuário

---

*Phase: 01-foundation*
*Completed: 2026-06-22*
