---
phase: 03-obs-connection
plan: 02
subsystem: obs-integration-ui
tags: [PySide6, QThread, non-blocking, OBSConnectThread, footer-status, UX-04, UX-02, UX-03]

requires:
  - phase: 03-obs-connection
    plan: 01
    provides: OBSConnectThread(QThread) com signals connected/failed/connecting + _classificar_erro()

provides:
  - MainWindow.obs_footer_label — QLabel de status OBS no rodapé (sempre visível em todas as abas)
  - MainWindow.testar_conexao_obs() — reescrito como não-bloqueante via OBSConnectThread
  - MainWindow.on_obs_conectando() — slot: atualiza labels para estado "Conectando..."
  - MainWindow.on_obs_conectado(obs_controller) — slot: sucesso, atribui engine.actions.obs
  - MainWindow.on_obs_falhou(mensagem) — slot: exibe mensagem acionável, mapeia resumo do rodapé
  - MainWindow._resumir_footer_obs(mensagem) — helper compartilhado de mapeamento detalhado→resumo
  - MainWindow._obs_connect_thread — referência viva da OBSConnectThread em andamento

affects: [03-03-engine-obs, ui/main_window.py]

tech-stack:
  added: []
  patterns:
    - Lazy import de OBSConnectThread dentro de testar_conexao_obs() (evita dependência circular na importação do módulo)
    - thread.finished.connect(thread.deleteLater) — liberação automática de memória ao completar (Armadilha 2)
    - self._obs_connect_thread = thread — referência viva mantida durante a tentativa (Armadilha 4)
    - Helper _resumir_footer_obs compartilhado entre on_obs_falhou (botão) e update_status (engine startup)

key-files:
  created: []
  modified:
    - ui/main_window.py

key-decisions:
  - "obs_footer_label inserido em QHBoxLayout status_row: status_label à esquerda, addStretch(), obs_footer_label à direita — alinhamento direito sem posicionamento absoluto"
  - "testar_conexao_obs() usa import local de OBSConnectThread (não no topo do módulo) para evitar ciclo de importação no startup"
  - "_resumir_footer_obs como método de instância (não função módulo-nível) pois é exclusivo da MainWindow e não precisa de reutilização em gesture_engine.py (03-03 usa _classificar_erro diretamente)"
  - "update_status() verifica 'OBS conectado' ANTES de startswith('OBS:') para capturar o caso de sucesso do startup da engine (Plano 03) sem sobrescrever o texto com _resumir_footer_obs"

metrics:
  duration: 10min
  completed: 2026-06-25
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1

status: complete
---

# Phase 03 Plan 02: Non-Blocking OBS Connection Button + Footer Status Summary

**Botão "Testar conexão" agora não-bloqueante via OBSConnectThread + indicador `obs_footer_label` sempre visível no rodapé da MainWindow**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-25T12:05:00-03:00
- **Completed:** 2026-06-25T12:15:00-03:00
- **Tasks:** 2/2
- **Files modified:** 1

## Accomplishments

- `obs_footer_label` adicionado ao rodapé da `MainWindow` em `QHBoxLayout status_row` (status geral à esquerda, status OBS à direita) — visível em todas as abas (UX-02 / D-05, D-06)
- `testar_conexao_obs()` reescrito: sem chamadas síncronas, usa `OBSConnectThread` com três signals conectados a slots dedicados; botão desabilitado durante tentativa (D-03); thread liberada via `deleteLater` (Armadilha 2); referência mantida em `_obs_connect_thread` (Armadilha 4)
- Três slots novos: `on_obs_conectando` (estado intermediário), `on_obs_conectado` (sucesso + atribuição à engine), `on_obs_falhou` (mensagem acionável + mapeamento de rodapé)
- `_resumir_footer_obs()` mapeia mensagens detalhadas para resumos compactos por palavra-chave (recusada→Offline, Senha→Senha incorreta, Timeout→Timeout, Endereço→Host inválido, fallback→Erro)
- `update_status()` estendido: preserva comportamento atual (status_label/log/health) e agora roteia mensagens com prefixo "OBS:" e "OBS conectado" ao `obs_footer_label` — fecha o caminho do startup da engine (Plano 03 ainda não implementado, mas a recepção já está preparada)
- `self._obs_connect_thread = None` inicializado em `__init__` junto de `self.engine = None`

## Task Commits

1. **Task 1: obs_footer_label no rodapé** — `dbeeb09` (feat)
2. **Task 2: testar_conexao_obs() não-bloqueante + slots + update_status** — `7abfce9` (feat)

## Files Created/Modified

- `ui/main_window.py` — modificado: +64 linhas, -14 linhas; obs_footer_label, status_row, testar_conexao_obs() reescrito, 3 slots novos, _resumir_footer_obs(), update_status() estendido, _obs_connect_thread inicializado

## Decisions Made

- `obs_footer_label` inserido em `QHBoxLayout status_row` com `addStretch()` entre os dois labels — alinha OBS status à direita sem posicionamento absoluto, sem quebrar layout existente de `log_title`/`log_view`/`controls_layout`
- Import de `OBSConnectThread` feito dentro de `testar_conexao_obs()` (lazy) para evitar possível ciclo de importação no topo do módulo (ui/main_window.py importa de engine/, que pode importar de integrations/)
- `_resumir_footer_obs` implementado como método de instância (não função módulo-nível): é específico da UI da MainWindow; o Plano 03 (`gesture_engine.py`) reutilizará `_classificar_erro()` diretamente (função módulo-nível do Plano 01), não este helper
- `update_status()` verifica `text == "OBS conectado"` antes de `text.startswith("OBS:")` para garantir que o caso de sucesso exibe "🟢 OBS: Conectado" (não passa pelo `_resumir_footer_obs`)

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado.

## Known Stubs

Nenhum — todos os métodos têm implementação real conectada a `OBSConnectThread` do Plano 01.

## Threat Flags

Nenhum novo surface além do planejado. Mitigações do threat model aplicadas:
- T-03-03: `on_obs_falhou` exibe apenas a mensagem classificada vinda de `_classificar_erro()` (via OBSConnectThread) — nunca `str(exc)` bruto; senha do campo nunca renderizada em label
- T-03-04: `test_obs_button.setEnabled(False)` durante a tentativa (D-03) impede acúmulo de threads; `finished→deleteLater` libera memória de cada thread

## Self-Check

- [x] `ui/main_window.py` modificado com todos os símbolos novos
- [x] `dbeeb09` existe no histórico git
- [x] `7abfce9` existe no histórico git
- [x] Verificação automatizada do plano retornou OK para ambas as tasks
- [x] `ast.parse(src)` não lançou exceção

## Self-Check: PASSED
