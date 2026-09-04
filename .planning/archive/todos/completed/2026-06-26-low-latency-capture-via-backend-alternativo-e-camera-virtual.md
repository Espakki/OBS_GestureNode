---
created: 2026-06-26T13:45:00.000Z
completed: 2026-06-27T00:32:00.000Z
title: Low-latency capture — backend alternativo e câmera virtual nativa no app
area: engine
resolves_phase: 13
resolution: spike-pyav
files:
  - core/camera.py
  - ui/tabs/geral_tab.py
---

## Problem

Logitech C920 (e similares) apresenta lag irredutível de ~40–50ms via DirectShow (`cv2.CAP_DSHOW`) por causa do pipeline MJPEG: encode no sensor + decode pelo driver via USB.

## Resolved — commit 619926a

**Solução aplicada:** PyAV (FFmpeg/DirectShow) com decode hardware MJPEG via dxva2. Elimina o lag sem necessidade de câmera virtual intermediária, sem OBS Virtual Cam, sem loop interno. A arquitetura final é mais simples que as etapas 2-3 propostas: uma única thread de captura via PyAV entrega frames decodificados pela GPU diretamente para o MediaPipe.

Câmera virtual (pyvirtualcam) continua sendo usada apenas para OUTPUT ao OBS — comportamento correto e sem mudança de stack.
