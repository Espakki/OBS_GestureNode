---
phase: 02-engine-camera
plan: "01"
subsystem: camera-pipeline
status: complete
tags: [camera, shutdown, non-blocking, logger, CAM-04]
requires: []
provides: [core/camera.py::CameraManager.ler_frame, core/camera.py::CameraManager.encerrar]
affects: [engine/gesture_engine.py]
tech_stack:
  added: []
  patterns: [grab/retrieve, try-except independentes, module-level logger]
key_files:
  modified: [core/camera.py]
decisions:
  - "grab()+retrieve() substitui cap.read() bloqueante — retorna mais cedo quando driver CAP_DSHOW trava"
  - "Dois blocos try/except independentes em encerrar() garantem que falha em close() nao impede release()"
  - "logger = get_logger(__name__) em nivel de modulo — mesmo padrao de engine/gesture_engine.py"
metrics:
  duration: "~15 minutos"
  completed: "2026-06-24"
  tasks_completed: 2
  tasks_total: 3
  files_modified: 1
---

# Phase 02 Plan 01: Camera Não-bloqueante e Shutdown Resiliente — Summary

CameraManager reescrito com leitura de frame não-bloqueante via grab()+retrieve() e shutdown resiliente com blocos try/except independentes. print() de diagnóstico migrado para logger do projeto.

## Tasks

| Task | Nome | Commit | Status |
|------|------|--------|--------|
| 1 | ler_frame() não-bloqueante via grab()+retrieve() | 83f4ec8 | Completa |
| 2 | encerrar() resiliente + print() para logger | 090411a | Completa |
| 3 | Checkpoint: Validação humana — câmera reabre 3x sem ocupada | — | APROVADO (2026-06-24) |

## Changes Made

### core/camera.py

**Task 1 — ler_frame() não-bloqueante (83f4ec8):**
- Substituiu `self.capture.read()` bloqueante por `self.capture.grab()` + `self.capture.retrieve()`
- `grab()` retorna False mais rapidamente quando o driver CAP_DSHOW não responde
- Fluxo: `capture is None` → (False, None); `grab()` False → (False, None); `retrieve()` False ou frame None → (False, None); caminho feliz → (True, frame_flipado)
- Nenhuma chamada a `.read()` permanece em `ler_frame()`

**Task 2 — encerrar() resiliente + logger (090411a):**
- Adicionou `from util.logger import get_logger` e `logger = get_logger(__name__)` em nível de módulo
- Substituiu `print(f"Câmera virtual ativa: ...")` por `logger.info("Câmera virtual ativa: %s", ...)`
- Reescreveu `encerrar()` com dois blocos try/except independentes:
  - Bloco 1: `capture.release()` isolado — falha logada via `logger.exception()`
  - Bloco 2: `virtual_camera.close()` isolado — falha logada via `logger.exception()`
- Falha em close() não impede release() de executar (mitiga T-02-02)

## Threat Mitigations Applied

| Threat ID | Status | Mitigation |
|-----------|--------|-----------|
| T-02-01 | Mitigado | grab()+retrieve() retorna mais cedo que read() bloqueante — loop da engine recupera self.running |
| T-02-02 | Mitigado | try/except separados garantem que capture.release() sempre executa mesmo se close() lançar exceção |
| T-02-03 | Aceito | ler_frame() valida ok e frame is None — conforme decisão do plano |

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

## Checkpoint Result

**Task 3 — Validação humana: APROVADA (2026-06-24)**

Winicius testou parar/reiniciar a engine 3x consecutivas sem fechar o app. Nenhuma das 3 reaberturas exibiu erro de câmera ocupada e o preview não ficou preto/congelado. CAM-04 satisfeito em hardware real.

## Verification Results

```
Task 1 — verificação AST:
  OK ler_frame grab/retrieve

Task 2 — verificação AST:
  OK encerrar resiliente + logger

Verificação completa combinada:
  TODAS AS VERIFICACOES PASSARAM
```

## Known Stubs

Nenhum stub presente. As alterações são funcionais e completas.

## Threat Flags

Nenhuma nova superfície de segurança introduzida neste plano.

## Self-Check

- [x] core/camera.py modificado e commitado (83f4ec8, 090411a)
- [x] grab() e retrieve() presentes em ler_frame()
- [x] .read() ausente de ler_frame()
- [x] 2 blocos try independentes em encerrar()
- [x] logger importado e instanciado em nível de módulo
- [x] Nenhum print() restante no arquivo
- [x] Commits existem: `git log --oneline` mostra 83f4ec8 e 090411a

## Self-Check: PASSED
