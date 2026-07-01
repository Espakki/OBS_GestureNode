---
created: 2026-06-25T00:37:02.957Z
completed: 2026-06-27T00:32:00.000Z
title: Investigar lag em resoluções altas com MediaPipe e webcams
area: engine
resolves_phase: 13
resolution: spike-pyav
files:
  - engine/gesture_engine.py
  - core/hand_tracker.py
  - core/camera.py
---

## Problem

O app apresenta lag visível na preview ao operar em 720p e 1080p, mas roda liso em 480p. O problema foi reproduzido em:
- Webcam genérica (resolução baixa) — sem lag em 480p
- Notebook integrado — comportamento similar
- Logitech C920 (2 unidades) — lag em 720p/1080p
- Outra Logitech (modelo não identificado)

Hardware do usuário: Xeon 2666v3 — problema de CPU descartado. Suspeita principal: pipeline/buffer do driver da webcam (ex.: Logitech MJPEG → decode → MediaPipe) acumula latência em resoluções altas.

## Solution

## Resolved — commit 619926a

Raiz do problema confirmada: OpenCV (CAP_DSHOW) fazia decode MJPEG via CPU no mesmo thread da engine.

**Solução aplicada:** PyAV (FFmpeg/DirectShow) como backend de captura. FFmpeg usa GPU para decode MJPEG via dxva2/d3d11va. MediaPipe passa a receber frames já decodificados — responsável apenas pela detecção. Lag eliminado completamente em 1080p 30fps. Compatibilidade total com webcams testada.
