---
created: 2026-06-27T00:32:37.772Z
title: Modo automático como padrão de fábrica
area: engine, ui
resolves_phase: 8
files:
  - engine/gesture_engine.py
  - ui/main_window.py
  - ui/tabs/geral_tab.py
  - config.json
---

## Problem

O modo atual padrão é `"test"`. O objetivo final do software é que o usuário abra, configure gestos, aperte iniciar e pronto — sem precisar entender modos. Isso exige que o modo `"automatico"` seja o padrão de fábrica.

## Decisão

Três modos existem:
- `"teste"` — detecção de gestos ativa, sem acionar OBS. Para o usuário validar seus gestos.
- `"manual"` — usuário configura câmera virtual / OBS manualmente (casos extremos).
- `"automatico"` — padrão de fábrica. O app gerencia tudo sozinho: captura via PyAV, expõe para o OBS via pyvirtualcam, executa gestos. Usuário não precisa tocar em nada além dos bindings.

## Solution

- Alterar `config.json`: `"modo": "automatico"` como default
- Garantir que a UI reflita os três modos com labels claros
- Modo automático não expõe opções técnicas de câmera para o usuário
