---
phase: 03-obs-connection
plan: 01
subsystem: obs-integration
tags: [obsws-python, PySide6, QThread, websocket, error-classification]

requires:
  - phase: 02-engine-camera
    provides: GestureEngine architecture, OBSController base class com ReqClient

provides:
  - OBSConnectThread(QThread) com signals connected/failed/connecting — reutilizável por UI e engine
  - _classificar_erro(exc) módulo-nível — classifica 4 tipos de erro para mensagens acionáveis
  - OBSController.connect() com handshake get_version() — elimina falso positivo de "conectado"

affects: [03-02-obs-ui, 03-03-engine-obs]

tech-stack:
  added: []
  patterns:
    - OBSConnectThread: thread-per-attempt (criada por tentativa, destruída ao completar — D-02)
    - isinstance chain ordering: ConnectionRefusedError/TimeoutError antes de OSError para capturar socket.gaierror corretamente
    - Exceção propaga sem try/except interno em connect() — caller classifica o erro

key-files:
  created:
    - integrations/obs_connect_thread.py
  modified:
    - integrations/obs_controller.py

key-decisions:
  - "get_version() inserido APÓS ReqClient() e ANTES de connected=True — sem try/except ao redor (exceção propaga ao caller)"
  - "WebSocketTimeoutException importada de 'websocket', não de 'obsws_python' (Armadilha 5 do RESEARCH.md)"
  - "Ordem exata do isinstance: ConnectionRefusedError → TimeoutError|WebSocketTimeout|OBSSDKTimeout → OSError → OBSSDKError → fallback"
  - "_classificar_erro é função módulo-nível (não método de OBSConnectThread) para reutilização por 03-03"

patterns-established:
  - "Thread-per-attempt: OBSConnectThread criada por tentativa de conexão, não reutilizada entre tentativas"
  - "Error classification: todas as mensagens de erro OBS passam por _classificar_erro() antes de chegar à UI"

requirements-completed: [OBS-01, UX-04, UX-03]

coverage:
  - id: D1
    description: "OBSController.connect() chama get_version() antes de setar connected=True — falso positivo eliminado"
    requirement: OBS-01
    verification:
      - kind: automated_ui
        ref: "python -c 'ast parse: get_version position < connected=True position'"
        status: pass
    human_judgment: false
  - id: D2
    description: "OBSConnectThread(QThread) existe com signals connected/failed/connecting e run() executando conexão fora do main thread"
    requirement: UX-04
    verification:
      - kind: automated_ui
        ref: "python -c 'from integrations.obs_connect_thread import OBSConnectThread; assert issubclass(OBSConnectThread, QThread)'"
        status: pass
    human_judgment: false
  - id: D3
    description: "_classificar_erro() mapeia 4 tipos de erro + fallback para mensagens acionáveis na ordem correta de isinstance"
    requirement: UX-03
    verification:
      - kind: automated_ui
        ref: "python -c '_classificar_erro testes: ConnectionRefusedError/TimeoutError/gaierror/OBSSDKError/ValueError'"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-06-25
status: complete
---

# Phase 03: OBS Connection — Plano 01 Summary

**Base não-bloqueante da conexão OBS: `OBSConnectThread(QThread)` com classificador de erros e handshake `get_version()` em `OBSController.connect()`**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-25T11:51:00-03:00
- **Completed:** 2026-06-25T11:53:08-03:00
- **Tasks:** 2/2
- **Files modified:** 2 (1 criado, 1 modificado)

## Accomplishments

- `OBSController.connect()` agora chama `self.cliente.get_version()` antes de `self.connected = True` — OBS inacessível lança exceção e `connected` permanece `False` (OBS-01 satisfeito)
- `OBSConnectThread(QThread)` criada como peça reutilizável: emite `connecting`, `connected(object)` ou `failed(str)` ao completar — pronta para wiring nos planos 02 e 03
- `_classificar_erro(exc)` com 5 branches na ordem correta (ConnectionRefusedError/TimeoutError antes de OSError) mapeia todos os cenários de erro para mensagens acionáveis em português (UX-03 satisfeito)

## Task Commits

1. **Task 1: Handshake get_version() em OBSController.connect()** — `915c707` (feat)
2. **Task 2: OBSConnectThread + _classificar_erro()** — `2b0b3c0` (feat)

## Files Created/Modified

- `integrations/obs_connect_thread.py` — novo: `OBSConnectThread(QThread)`, `_classificar_erro()`, imports corretos de `websocket.WebSocketTimeoutException`
- `integrations/obs_controller.py` — modificado: +3 linhas inserindo `self.cliente.get_version()` no corpo de `connect()`

## Decisions Made

- `get_version()` sem try/except interno — a exceção propaga ao caller (OBSConnectThread.run()) que é quem classifica e emite o erro
- `WebSocketTimeoutException` importada de `websocket` (não de `obsws_python`) conforme Armadilha 5 do RESEARCH.md
- `_classificar_erro` como função módulo-nível (não método da classe) para reutilização direta pelo Plano 03 em `gesture_engine.py`

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado. Commits em ordem ligeiramente invertida (Task 2 antes de Task 1) sem impacto funcional pois modificam arquivos distintos.

## Issues Encountered

Nenhum problema durante a execução. Worktree foi criado a partir de commit anterior ao esperado (`70c1de0` em vez de `8aca0ec`) — resolvido via cherry-pick dos dois commits para o main, produzindo o mesmo resultado sem conflitos.

## Next Phase Readiness

- **03-02 pronto para execução:** `OBSConnectThread` disponível para wiring no botão "Testar conexão" da `OBSTab` e no indicador de status do rodapé da `MainWindow`
- **03-03 pronto para execução:** `_classificar_erro()` disponível para reutilização em `GestureEngine._connect_obs()` sem duplicação
- Sem bloqueadores

---
*Phase: 03-obs-connection*
*Completed: 2026-06-25*
