---
phase: 03-obs-connection
plan: "03"
subsystem: integrations/engine
status: complete
tags: [obs, error-classification, gesture-engine, startup-path]
dependency_graph:
  requires: [03-01]
  provides: [_connect_obs-classified-errors]
  affects: [engine/gesture_engine.py]
tech_stack:
  added: []
  patterns: [import-reuse, classified-error-emission]
key_files:
  created: []
  modified:
    - engine/gesture_engine.py
decisions:
  - "Reutilizar _classificar_erro de obs_connect_thread (sem duplicar lógica) — consistente com D-07 do CONTEXT.md"
  - "Não criar OBSConnectThread dentro de _connect_obs() — a engine já é um QThread de background, seria overhead desnecessário"
  - "Prefixo 'OBS: ' na mensagem emitida para que update_status() em main_window.py roteie ao obs_footer_label (Plano 02)"
metrics:
  duration: "5min"
  completed: "2026-06-25T21:49:38Z"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 1
---

# Phase 03 Plan 03: OBS Startup Error Classification Summary

**One-liner:** `_connect_obs()` refatorado para importar e usar `_classificar_erro` de `obs_connect_thread`, emitindo mensagens acionáveis com prefixo `"OBS: "` no caminho de exceção do startup da engine.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Refatorar _connect_obs() com classificação de erro | a4fa652 | engine/gesture_engine.py |

---

## What Was Built

### Task 1 — Refatorar `_connect_obs()` (OBS-01 / UX-03 / D-07)

**Problema:** O caminho de conexão do startup da engine emitia a mensagem genérica `"Falha ao conectar OBS"` via `status_changed`, enquanto o caminho do botão (Plano 01 — `OBSConnectThread`) já emitia mensagens acionáveis classificadas por tipo (conexão recusada, timeout, senha incorreta etc.). Essa inconsistência violava UX-03 e D-07.

**Solução:** Duas mudanças cirúrgicas em `engine/gesture_engine.py`:

1. **Novo import** no bloco de imports do topo:
   ```python
   from integrations.obs_connect_thread import _classificar_erro
   ```

2. **Bloco `except` de `_connect_obs()`** — substituição da mensagem genérica:
   ```python
   # Antes:
   self.status_changed.emit("Falha ao conectar OBS")

   # Depois:
   mensagem = _classificar_erro(exc)
   self.status_changed.emit(f"OBS: {mensagem}")
   ```

**O que permanece inalterado:**
- Early-return `if self.config.get("modo") != "obs": return`
- Reset inicial `self.obs = None` / `self.actions.obs = None`
- Caminho de sucesso: `self.obs.connect()` (com handshake `get_version()` via Plano 01) + emit `"OBS conectado"` + `self.actions.obs = self.obs`
- `logger.exception("Falha ao conectar OBS: %s", exc)` mantém detalhe no log local (T-03-05)
- Assinatura `def _connect_obs(self)` e chamada `self._connect_obs()` em `run()` intactas
- Nenhum `OBSConnectThread` instanciado na engine (D-07: engine já é QThread de background)

**Verificações executadas:**
- AST parse: import presente, `_classificar_erro(exc)` no corpo, sem emit genérico antigo, prefixo `OBS:` presente, sem `OBSConnectThread` no corpo, `"OBS conectado"` no caminho de sucesso
- Import real no venv: `python -c "import engine.gesture_engine"` → OK sem import circular

---

## Requirements Closed

| Req ID | Description | Status |
|--------|-------------|--------|
| OBS-01 | Handshake get_version() antes de marcar conectado | Fechado (herdado via connect() do Plano 01, agora também no startup) |
| UX-03 | Mensagens de erro acionáveis e classificadas por tipo | Fechado (ambos os caminhos — botão e engine — agora usam _classificar_erro) |

---

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

---

## Threat Model Coverage

| Threat ID | Disposição | Implementado |
|-----------|------------|--------------|
| T-03-05 (Information Disclosure) | mitigate | `logger.exception` mantém detalhe só no log local; `status_changed` emite apenas a mensagem classificada, nunca `str(exc)` bruto |
| T-03-06 (DoS — engine thread bloqueada até 5s) | accept | Aceito: a engine é QThread de background; UI não é afetada |
| T-03-SC (Tampering — novos pacotes) | accept | Nenhum `pip install` — apenas import interno de módulo já existente (Plano 01) |

---

## Known Stubs

Nenhum.

---

## Threat Flags

Nenhum novo surface de segurança introduzido. O import de `_classificar_erro` é interno ao projeto (módulo `integrations.obs_connect_thread` criado no Plano 01).

---

## Self-Check: PASSED

- [x] `engine/gesture_engine.py` modificado e commitado em a4fa652
- [x] Import `from integrations.obs_connect_thread import _classificar_erro` presente
- [x] `_classificar_erro(exc)` chamado no bloco except de `_connect_obs()`
- [x] Emit `f"OBS: {mensagem}"` substitui a mensagem genérica
- [x] Import circular ausente (verificado no venv)
- [x] Assinatura e chamada em `run()` inalteradas
- [x] `OBSConnectThread` não instanciado na engine
