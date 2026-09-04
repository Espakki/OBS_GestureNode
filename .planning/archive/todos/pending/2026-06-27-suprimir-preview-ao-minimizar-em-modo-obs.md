---
created: 2026-06-27T00:32:37.772Z
title: Suprimir preview da câmera ao minimizar janela (modo OBS ativo)
area: ui, engine
resolves_phase: 15
files:
  - ui/main_window.py
  - engine/gesture_engine.py
---

## Problem

Quando o usuário minimiza o app enquanto está em modo ativo (OBS/automático), o software continua renderizando frames na preview Qt mesmo sem ninguém vendo. Isso consome processamento desnecessariamente — a câmera está rodando para o OBS via pyvirtualcam, e fazer render na UI por cima é trabalho duplo.

## Decisão

Quando a janela for minimizada em modo ativo:
- A preview de câmera na UI **some** (para de renderizar/exibir)
- O feed ao OBS via pyvirtualcam **continua normalmente** — o OBS não é afetado
- Ao restaurar a janela, a preview volta automaticamente

## Solution

- Conectar `QMainWindow.changeEvent` (ou `windowStateChanged`) ao evento de minimizar
- Quando `Qt.WindowMinimized`: parar de emitir `frame_ready` para o widget de preview, OU ignorar o sinal no slot da UI
- Quando restaurado (`not Qt.WindowMinimized`): retomar exibição
- A engine continua rodando normalmente — só o `frame_ready → UI slot` é desconectado/reconectado
- pyvirtualcam.send() dentro de CameraManager não é afetado
