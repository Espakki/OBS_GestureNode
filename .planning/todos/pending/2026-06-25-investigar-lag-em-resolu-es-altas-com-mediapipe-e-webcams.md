---
created: 2026-06-25T00:37:02.957Z
title: Investigar lag em resoluções altas com MediaPipe e webcams
area: engine
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

**Hipóteses a investigar:**
1. A câmera entrega frames em MJPEG comprimido que o OpenCV precisa decodificar — custo cresce com resolução
2. MediaPipe roda inferência na resolução original antes do resize em `hand_tracker.py` (Plan 02-03 faz resize para 640×480, mas o frame já entra grande)
3. Buffer do DirectShow (`cv2.CAP_DSHOW`) acumula frames não processados quando a engine é mais lenta que a câmera, causando latência acumulada
4. `process_fps` cap (Plan 02-05) descarta frames mas não drena o buffer — câmera continua enchendo

**Experimento sugerido pelo usuário:** Capturar via software intermediário (ex.: OBS Virtual Camera ou ManyCam) e redirecionar o stream virtual para o app — isola se o problema é na conexão direta com hardware ou na resolução em si.

**Impacto:** Crítico para o escopo do projeto — streamers precisam de qualidade visual (720p+). Sem resolução disso, adaptabilidade com webcams do mercado fica comprometida.

## Solution

1. **Diagnóstico por isolamento** — testar com fonte de vídeo virtual (câmera virtual de outro software) para separar problema de hardware vs. pipeline da engine
2. **Profile da engine** — medir tempo de cada etapa: `cap.read()`, decode, resize, MediaPipe inference, emit frame
3. **Buffer drain** — investigar se é necessário chamar `cap.grab()` em loop para descartar frames velhos antes de `cap.retrieve()`
4. **Decoupled frame buffer** — separar thread de captura (drena câmera continuamente) de thread de processamento (pega frame mais recente) para evitar acúmulo de latência
5. Se causa for MJPEG: tentar forçar formato `YUYV` ou `NV12` via `cap.set(cv2.CAP_PROP_FOURCC, ...)` — evita decode extra
6. Alvo mínimo: 720p rodando sem lag perceptível com webcam Logitech C920
