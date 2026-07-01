---
created: 2026-06-27T00:32:37.772Z
title: OBS Virtual Cam — modos automático e manual dentro de Configurações Avançadas
area: engine, ui
resolves_phase: 13
files:
  - core/camera.py
  - engine/gesture_engine.py
  - ui/tabs/geral_tab.py
  - config.json
---

## Problem

O modo como o app expõe frames ao OBS via câmera virtual precisa de dois níveis de controle:

**Automático (padrão):** O app gerencia pyvirtualcam internamente. O usuário não configura nada — o software decide device, resolução e fps da câmera virtual baseado na câmera física detectada.

**Manual (para casos extremos):** Se o comportamento automático apresentar problemas (device conflict, driver incompatível, OBS não detecta a câmera virtual), o usuário pode especificar manualmente: nome do device virtual, resolução, fps. Fluxo mais mecânico mas necessário como válvula de escape.

## Solution

- Adicionar campo `"virtual_cam_mode": "auto" | "manual"` no config.json
- No modo auto: `CameraManager` detecta o device pyvirtualcam disponível automaticamente
- No modo manual: usa `virtual_camera_device` do config (comportamento atual)
- Na UI (dentro de Configurações Avançadas): radio button Automático / Manual
- Manual expande campos adicionais: nome do device, resolução override
