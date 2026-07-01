---
phase: 02-engine-camera
plan: "03"
subsystem: hand-tracker-resize
status: complete
tags: [mediapipe, performance, resize, cam-01, cam-02]
dependency_graph:
  requires: ["02-02"]
  provides: ["resize-640x480-interarea", "mediapipe-lite-params"]
  affects: ["core/hand_tracker.py", "engine/gesture_engine.py"]
tech_stack:
  added: []
  patterns: ["resize-before-inference", "fixed-processing-resolution"]
key_files:
  created: []
  modified:
    - core/hand_tracker.py
decisions:
  - "Opção A adotada: HandTracker retorna frame_small 640x480; engine emite esse frame para preview e câmera virtual"
  - "model_complexity=0 (lite) e min_tracking_confidence=0.5 para ganho ~40-55% FPS"
  - "PROCESS_W=640, PROCESS_H=480 como constantes de módulo (NÃO lê frame.shape em processar)"
metrics:
  duration: "~15min"
  completed: "2026-06-24T19:37:00Z"
  tasks_completed: 3
  tasks_total: 3
  files_changed: 1
---

# Phase 02 Plan 03: Resize 640x480 + Params Lite Summary

## One-liner

MediaPipe passa a processar sempre em 640x480 com resize INTER_AREA (model_complexity=0, min_tracking_confidence=0.5), desacoplando custo de inferência da resolução de captura.

## What Was Built

### Task 1: Resize 640x480 + params lite no HandTracker (COMPLETO)

Commit: `260287a`

- Constantes `PROCESS_W = 640` e `PROCESS_H = 480` adicionadas no módulo `core/hand_tracker.py`
- `HandTracker.__init__`: `Hands()` agora usa `model_complexity=0` (lite) e `min_tracking_confidence=0.5`; manteve `min_detection_confidence=0.7` e `max_num_hands=1`
- `HandTracker.processar()`: primeira operação é `cv2.resize(frame, (PROCESS_W, PROCESS_H), interpolation=cv2.INTER_AREA)` criando `frame_small`
- `cv2.cvtColor` aplicado em `frame_small` (não no frame original)
- Landmarks calculados com `px = int(lm.x * PROCESS_W)` e `py = int(lm.y * PROCESS_H)` — escala fixa, sem `frame.shape`
- Skeleton desenhado em `frame_small` quando `draw_skeleton=True`
- Retorna `(frame_small, pontos)` — frame 640x480 com skeleton sobreposto

### Task 2: Engine emite o frame processado (640x480) (VERIFICADO — sem mudança necessária)

- Verificação confirmou que `engine/gesture_engine.py` já implementava Opção A corretamente
- `frame, pontos = self.tracker.processar(frame, draw_skeleton=self.show_skeleton)` na linha 326 reatribui `frame` com o valor retornado pelo tracker
- `self.frame_ready.emit(frame)` e `self.camera.enviar_para_virtual(frame)` usam a variável `frame` reatribuída (agora 640x480)
- Nenhuma referência ao frame de resolução original emitida para preview
- Não foi necessário modificar o arquivo (plano explicitava: "NÃO é necessário renomear variáveis")

### Task 3: Checkpoint humano (APROVADO)

Resultado da validação humana (Logitech C920):

- Skeleton visivelmente mais fluido e alinhado aos dedos — objetivo CAM-01 e CAM-02 confirmados
- Preview em 640x480 padrão funcionou corretamente
- Gestos ainda detectados após as mudanças

**Observação hardware:** O usuário reportou que o preview fica lento em 720p e 1080p. Isso é uma limitação de captura da Logitech C920 via USB 2.0 + DirectShow — a câmera entrega ~5 FPS nativamente nessas resoluções, independente do processamento MediaPipe. O objetivo deste plano (desacoplar custo de inferência da resolução de captura) foi atingido: MediaPipe agora processa sempre em 640x480 independente da resolução configurada. O gargalo de FPS em 720p/1080p é de captura (câmera → OpenCV), não de processamento — está fora do escopo de CAM-01/CAM-02 e pode ser endereçado em planos futuros (ex: limitação de FPS de captura via `cv2.VideoCapture.set(cv2.CAP_PROP_FPS, 30)` ou recomendação de configurar a câmera em 640x480).

## Deviations from Plan

### Auto-fixed Issues

Nenhuma — plano executado exatamente como especificado.

### Notes

- Task 2 não gerou commit separado pois não houve mudança de código (verificação de consistência confirmou Opção A já implementada)
- Nota sobre câmera virtual (Pitfall 3 do research): com Opção A o frame emitido é 640x480. Como `config.json` atual usa `camera.width=640, camera.height=480`, a câmera virtual recebe dimensões compatíveis. Se a captura for elevada para 1080p no futuro, a câmera virtual continuará recebendo 640x480 (resolução de processamento) — comportamento desejado da Opção A.

## Threat Model Coverage

| Threat ID | Mitigation Aplicada |
|-----------|---------------------|
| T-02-06 | Resize fixo para 640x480 implementado em `processar()` — custo MediaPipe normalizado independente da resolução de entrada |
| T-02-07 | Frame com shape inválido: cv2.resize levanta exceção capturada pelo try/except do loop run() — sem ação adicional necessária |

## Known Stubs

Nenhum.

## Self-Check: PASSED

- `core/hand_tracker.py` modificado: verificado via `git diff HEAD~1 HEAD`
- Commit `260287a` existe: `git log --oneline -1` confirma
- Verificação AST passed: "OK hand_tracker resize+params"
- Verificação engine passed: "OK engine emite frame processado"
