---
phase: 01-foundation
plan: "01"
subsystem: infra
tags: [pip, requirements, dependencies, pygrabber, mediapipe, pyside6, opencv]

requires: []
provides:
  - "requirements.txt com 7 dependencias pinadas com == para Python 3.10.11"
  - "pygrabber==0.2 adicionado e verificado como legitimo via pypi.org"
  - "mediapipe==0.10.14 mantido inalterado (constraint critico)"
  - "install reproduzivel validado em venv limpo pelo usuario"
affects:
  - "02-engine-camera"
  - "03-obs-connection"
  - "todas as fases subsequentes que dependem do ambiente de desenvolvimento"

tech-stack:
  added:
    - "pygrabber==0.2 — enumeracao de dispositivos DirectShow no Windows"
  patterns:
    - "Pinagem exata com == para todas as dependencias (sem ranges >= ou ~=)"
    - "Comentario # Python 3.10.11 na primeira linha do requirements.txt"

key-files:
  created: []
  modified:
    - "requirements.txt — 7 dependencias pinadas + comentario de versao Python"

key-decisions:
  - "Usar == exato em todas as dependencias (sem ranges) para garantir installs reproduziveis (DEP-01, DEP-02)"
  - "Substituir linha invalida 'python version == 3.10.11' por comentario '# Python 3.10.11' (D-06)"
  - "pygrabber==0.2 verificado via pypi.org antes de adicionar — gate de legitimidade humano obrigatorio (T-01-SC)"
  - "mediapipe==0.10.14 mantido exatamente como estava — constraint critico do CLAUDE.md (D-04)"
  - "opencv-contrib-python 4.13.0.92 coexiste como dep transitiva do mediapipe; sem conflito de install"

patterns-established:
  - "Gate de legitimidade humano (checkpoint:human-verify blocking-human) antes de adicionar pacotes PyPI nao verificados"
  - "Validacao de install em venv limpo como criterio de aceitacao final para mudancas em requirements.txt"

requirements-completed: [DEP-01, DEP-02]

duration: ~15min (execucao efetiva, excluindo tempo de espera humano)
completed: "2026-06-22"
status: complete
---

# Phase 01 Plan 01: Requirements Pinning Summary

**requirements.txt reparado com 7 dependencias pinadas via ==, pygrabber==0.2 adicionado e validado em venv limpo — installs reproduziveis garantidos para Python 3.10.11**

## Performance

- **Duration:** ~15 min (execucao efetiva; gates humanos aguardaram confirmacao externa)
- **Started:** 2026-06-22T21:00:00-03:00
- **Completed:** 2026-06-22T22:10:00-03:00
- **Tasks:** 3 (2 checkpoints human-verify + 1 auto)
- **Files modified:** 1

## Accomplishments

- Todas as 7 dependencias pinadas com `==` exato — nenhum range `>=` ou `~=` restante
- `pygrabber==0.2` adicionado apos verificacao de legitimidade via pypi.org (gate humano Task 1)
- Linha invalida `python version == 3.10.11` removida e substituida por comentario correto
- `mediapipe==0.10.14` mantido inalterado (constraint critico do CLAUDE.md respeitado)
- Install validado em venv limpo pelo usuario — `pip install -r requirements.txt` sem erro de resolucao

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Verificar legitimidade do pygrabber** - checkpoint human-verify (sem commit de codigo — gate aprovado pelo usuario)
2. **Task 2: Pinar dependencias e adicionar pygrabber** - `7ece76d` (feat)
3. **Task 3: Validar install em venv limpo** - checkpoint human-verify (sem commit de codigo — validacao pelo usuario)

**Plan metadata:** (pendente — este e o commit de documentacao)

## Files Created/Modified

- `requirements.txt` — Reparado: 7 dependencias pinadas com `==`, `pygrabber==0.2` adicionado, linha invalida `python version == 3.10.11` removida, comentario `# Python 3.10.11` na primeira linha

## Decisions Made

- **Gate de legitimidade obrigatorio para pygrabber:** O pacote estava marcado como `[ASSUMED]`/`SUS` na auditoria de dependencias (motivo tecnico: API do PyPI nao retorna contagem de downloads, nao e indicativo de risco real). O plano exigiu confirmacao humana via pypi.org antes de qualquer write — Winicius confirmou que `pygrabber==0.2` e o pacote correto de github.com/andreaschiavinato/python_grabber.

- **Coexistencia de opencv-python e opencv-contrib-python:** Durante o install do usuario, `mediapipe==0.10.14` puxou `opencv-contrib-python==4.13.0.92` como dependencia transitiva, coexistindo com `opencv-python==4.10.0.84`. O install completou sem erro — comportamento esperado e documentado.

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito. Os dois checkpoints human-verify foram gates planejados, nao desvios.

## Issues Encountered

**Coexistencia de opencv-python e opencv-contrib-python:** `mediapipe==0.10.14` declarou `opencv-contrib-python` como dependencia transitiva, resultando em duas variantes do opencv instaladas. O pip nao reportou conflito de versao e o install completou sem erro. Este comportamento e conhecido para mediapipe 0.10.x e nao requer acao — documentado para referencia das fases seguintes (02-engine-camera).

## User Setup Required

Nenhuma configuracao de servico externo necessaria. Para reproduzir o ambiente:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Next Phase Readiness

- Ambiente de dependencias estavel e reproduzivel — pronto para Phase 02 (Engine & Camera)
- `pygrabber==0.2` disponivel para enumeracao de dispositivos DirectShow em `ui/main_window.py`
- Nenhum bloqueador identificado para as fases subsequentes

## Self-Check

- [x] `requirements.txt` existe e contem 7 dependencias pinadas com `==`
- [x] Commit `7ece76d` existe no historico git
- [x] Install validado em venv limpo pelo usuario (Task 3 aprovada)
- [x] `mediapipe==0.10.14` inalterado
- [x] `pygrabber==0.2` presente

**Self-Check: PASSED**

---
*Phase: 01-foundation*
*Completed: 2026-06-22*
