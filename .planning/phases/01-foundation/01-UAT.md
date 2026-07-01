---
status: complete
phase: 01-foundation
started: 2026-06-23T20:00:00-03:00
updated: 2026-06-23T21:20:00-03:00
---

## Current Test

[testing complete]

## Tests

### 1. Edição concorrente de duas abas com engine rodando

expected: Nenhum KeyError no console por ~30s de edição rápida de hold_time/cooldown/enabled enquanto a engine processa frames; gestos detectados acionam a ação correta
steps: |
  1. Iniciar o app (modo "test" ou "obs")
  2. Ligar a câmera/engine
  3. Alternar rapidamente entre abas Geral e Gestos editando sliders e campos por ~30s
  4. Observar o console — nenhum traceback de KeyError deve aparecer
  5. Confirmar que os gestos detectados disparam a ação correta (não o gesto de outra binding)
result: pass
note: "Camera freezes briefly when gesture has no binding configured — gesto sem binding trava câmera. Observação para melhoria futura, fora do escopo da Phase 1."

### 2. Verificar impacto de CR-01 (ROCK/TRÊS/QUATRO mismatch)

expected: |
  Gestos Rock, Três e Quatro configurados com ação na UI devem disparar quando feitos.
  Se não dispararem, CR-01 está bloqueando e precisa de fix antes de Phase 2.
  Se o usuário nunca configurou esses 3 gestos, o impacto é zero agora mas ainda é defeito latente.
steps: |
  1. Na aba Gestos, configurar Rock, Três e Quatro com uma ação qualquer (ex: hotkey)
  2. Executar os gestos na câmera
  3. Verificar se as ações disparam
  NOTE: Este item está fora dos success criteria da Phase 1 (ENG-03 verifica identidade
  do dict, não os valores das aliases). A decisão de tratar como blocker é do developer.
result: issue
reported: "Ao colocar uma tecla de atalho e mudar para outro gesto, ele não salva automaticamente. Quando volta para o gesto está sem nada."
severity: major

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0
blocked: 0

## Diagnosis

### Gap 1 — Hotkey não salva ao navegar entre gestos

root_cause: |
  HotkeyLineEdit._finish_capture() chama setText() com blockSignals(True) ativo.
  O sinal textChanged nunca dispara. O sinal hotkeyCommitted existe e emite
  corretamente, mas não está conectado a on_current_gesture_changed em main_window.py.
  Resultado: digitar hotkey via captura não persiste na config.
fix: "Adicionar self.hotkey_edit.hotkeyCommitted.connect(self.on_current_gesture_changed) em main_window.py após linha 482"
file: ui/main_window.py
severity: major

## Gaps

- truth: "Configurar hotkey para um gesto e mudar de gesto deve persistir a binding — ao voltar, o campo deve mostrar a tecla salva"
  status: failed
  reason: "User reported: binding some via hotkey e ao mudar de gesto, ao voltar o campo está vazio — não salva automaticamente ao navegar entre gestos"
  severity: major
  test: 2
  artifacts: []
  missing: []
