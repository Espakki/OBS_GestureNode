---
created: 2026-06-27T00:32:37.772Z
title: Configurações de câmera → painel "Configurações Avançadas" oculto
area: ui
resolves_phase: 14
files:
  - ui/tabs/geral_tab.py
  - ui/main_window.py
---

## Problem

O painel atual de configurações de câmera (índice, resolução, fps, tipo de captura, câmera virtual) fica exposto por padrão na aba Geral. Isso cria fricção desnecessária — o modo automático deve funcionar sem o usuário precisar tocar nessas opções.

## Decisão

O painel vira "Configurações Avançadas" — fica oculto por padrão, expandido apenas quando o usuário clica. Conteúdo do painel avançado:
- Resolução (width × height)
- FPS
- ~~Tipo de captura (MJPEG/YUY2)~~ — REMOVIDO (PyAV cuida automaticamente)
- Modo OBS Virtual Cam: Automático / Manual

O campo "tipo de captura" é eliminado porque PyAV com FFmpeg negocia o formato diretamente com o driver — o usuário nunca precisa saber disso.

## Solution

- Envolver os widgets de câmera em um `QGroupBox` colapsável ou `QStackedWidget` com toggle
- Label do botão: "Configurações Avançadas ▼ / ▲"
- Estado padrão: fechado
- Remover widget de seleção de tipo de captura da UI
