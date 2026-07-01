---
created: 2026-06-26T13:45:00.000Z
title: Detecção de 2 mãos e gestos combinados
area: engine, ui
resolves_phase: 9
files:
  - core/hand_tracker.py
  - core/gesture_detector.py
  - engine/gesture_engine.py
  - ui/tabs/geral_tab.py
  - ui/tabs/gestos_tab.py
---

## Feature

Adicionar modo de detecção com 2 mãos. O usuário escolhe na aba Geral:
- **1 mão** (padrão atual): só gestos com uma mão, comportamento idêntico ao atual
- **2 mãos**: MediaPipe rastreia ambas as mãos; aba Gestos exibe gestos de mão única E gestos combinados (duas mãos simultaneamente)

## Comportamento esperado

### Aba Geral
- Radio ou toggle: "Mãos detectadas: 1 / 2"
- Quando 2 mãos selecionado, aparece seção de gestos combinados na aba Gestos

### Aba Gestos com 2 mãos ativo
- Seção "Gestos com 1 mão" (esquerda e/ou direita)
- Seção "Gestos combinados (2 mãos)" com gestos pré-definidos
- Exemplos de gestos combinados pré-definidos:
  - Ambas as mãos abertas (OPEN_PALM + OPEN_PALM)
  - Polegares para cima em ambas as mãos (THUMBS_UP + THUMBS_UP)
  - Mão esquerda fechada + direita aberta (FIST + OPEN_PALM)
- Permitir o usuário criar combinações personalizadas (escolher gesto da mão esquerda + gesto da mão direita)

## Notas de implementação

- MediaPipe 0.10.14 já suporta `max_num_hands=2` em `mp.solutions.hands.Hands` — sem atualização de dependência
- `HandTracker` retorna lista de landmarks por mão — já estruturado para múltiplas mãos
- `GestureDetector` precisa ser estendido para receber 2 conjuntos de landmarks e retornar gesto combinado
- `GestureEngine` precisa agregar resultados de 2 mãos antes de passar para `ActionManager`
- Config `config.json` precisa de novo campo `"max_maos": 1` (padrão) e estrutura de bindings para gestos combinados
- Cooldown e hold_time se aplicam ao gesto combinado como unidade (não individualmente por mão)

## Impacto

Feature diferencial — poucos apps de gesto suportam combinações de 2 mãos. Dobra o número de ações configuráveis sem complexidade adicional para o usuário que usa 1 mão.
