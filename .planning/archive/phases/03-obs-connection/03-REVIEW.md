---
phase: 03-obs-connection
reviewed: 2026-06-25T21:58:00-03:00
depth: standard
files_reviewed: 4
files_reviewed_list:
  - engine/gesture_engine.py
  - integrations/obs_connect_thread.py
  - integrations/obs_controller.py
  - ui/main_window.py
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-25T21:58:00-03:00
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 03 added non-blocking OBS WebSocket connection infrastructure: `OBSConnectThread` (a QThread that connects and emits signals), `_classificar_erro()` (error classifier), `OBSController.get_version()` handshake, and UI wiring in `MainWindow` (`testar_conexao_obs`, footer label, result slots). The `GestureEngine._connect_obs()` was refactored to emit classified error strings.

The architecture is sound. The critical issues are: a dead code path inside the gesture dispatch loop that can never execute (logic bug producing silent action-skipping), an `OBSController` instance leak when `testar_conexao_obs` is called rapidly in succession, and a missing `closeEvent` that leaves the connect thread running after the window closes. Four warnings cover a `disconnect()` that does not close the underlying WebSocket, a race condition when the UI injects `obs_controller` into a running engine, double-setting the "Conectando…" state, and `restart_engine()` not waiting for stop to complete before re-starting. Two info items cover the duplicated gesture-cfg construction block and the `_probe_opencv_camera_indexes` stderr suppression side-effect.

---

## Critical Issues

### CR-01: Dead Legacy Fallback Inside `_connect_obs` Guard — Action Never Fires for Legacy Gestures

**File:** `engine/gesture_engine.py:389`

**Issue:** Inside the `if (tempo_atual - ultimo_disparo) > cooldown:` block, there is a second `if not gesture_cfg and nome_cena:` guard at line 389. At this point `gesture_cfg` was already populated by the earlier fallback at lines 364–375. If the fallback succeeded, `gesture_cfg` is truthy, so this second block never executes. If the fallback failed (no `mapa_cenas` entry and no `bindings` entry), `gesture_cfg` is an empty dict `{}` — falsy — but `nome_cena` is also `None` (line 387), so the block still never executes. The path `gesture_cfg = {...}` at lines 390–398 is **unreachable dead code**. As a consequence, in the edge case where a gesture has a `mapa_cenas` entry but the first fallback (line 364 check) somehow does not run (e.g. the property getter returns a snapshot that already has the key removed between the two reads due to a concurrent write), `self.actions and gesture_cfg` at line 400 evaluates to `False`, the action is silently skipped, and `action_submitted` stays `False` — meaning the cooldown timestamp is **not** updated. The gesture then fires on every subsequent frame until the cooldown expires naturally from any *other* gesture path.

The real bug is that the two `gesture_cfg` lookup / fallback blocks at lines 363–375 and 386–398 are duplicated with subtly different conditions, creating a confusing code path that is provably broken for one of the two reads.

**Fix:** Remove the second duplicate block (lines 387–398) entirely. The first fallback (lines 363–375) is sufficient and always runs first.

```python
# Remove lines 387-398 entirely. The block after the cooldown guard becomes:
if self.actions and gesture_cfg:
    try:
        scene = gesture_cfg.get("scene", "").strip()
        ...
```

---

### CR-02: `OBSController` Instance Leaked When `testar_conexao_obs` Is Called Rapidly

**File:** `ui/main_window.py:984–990`

**Issue:** `testar_conexao_obs` creates a new `OBSConnectThread` and stores it in `self._obs_connect_thread` (line 989). If the user clicks "Testar" a second time before the first thread finishes, the reference to the old thread is **overwritten at line 989** before the old thread has completed. The old thread holds a reference to an `OBSController` which holds a `ReqClient` WebSocket connection. When the old thread eventually finishes and its `connected` or `failed` signal fires, the slot calls `self._obs_connect_thread = None` — but that now clears the *new* thread's reference, not the old one. The old thread's signals fire on the UI's `MainWindow` instance (cross-thread signal), potentially calling `on_obs_conectado` with a stale `OBSController` *after* the new connection result has already been handled.

Additionally, if the new thread fails and clears `self._obs_connect_thread = None`, but the old thread then emits `connected`, the UI will report success for a connection the user did not intend.

**Fix:** Abort (or ignore signals from) the previous thread before starting a new one.

```python
def testar_conexao_obs(self):
    from integrations.obs_connect_thread import OBSConnectThread

    # Cancel any in-flight attempt: disconnect slots so stale signals are ignored.
    if self._obs_connect_thread is not None:
        try:
            self._obs_connect_thread.connected.disconnect()
            self._obs_connect_thread.failed.disconnect()
            self._obs_connect_thread.connecting.disconnect()
        except Exception:
            pass
        self._obs_connect_thread = None

    host = self.obs_host.text().strip()
    port = self.obs_port.value()
    password = self.obs_password.text()

    self.test_obs_button.setEnabled(False)
    self.obs_status_label.setText("Conectando...")
    self.obs_footer_label.setText("⏳ OBS: Conectando...")

    thread = OBSConnectThread(host, port, password)
    thread.connecting.connect(self.on_obs_conectando)
    thread.connected.connect(self.on_obs_conectado)
    thread.failed.connect(self.on_obs_falhou)
    thread.finished.connect(thread.deleteLater)
    self._obs_connect_thread = thread
    thread.start()
```

---

### CR-03: No `closeEvent` — `OBSConnectThread` Can Run Past Window Destruction

**File:** `ui/main_window.py` (no `closeEvent` defined)

**Issue:** `MainWindow` has no `closeEvent` override. If the user closes the window while `OBSConnectThread` is connecting (can take up to 5 seconds — the `timeout=5` in `OBSController.connect()`), the thread continues running and its signals (`connected`, `failed`) will fire on the already-deleted `MainWindow` C++ object. In PySide6 this causes a **RuntimeError: Internal C++ object (MainWindow) already deleted** crash, or worse, silent memory corruption if the GC has not yet collected the Python wrapper. The same issue applies to `GestureEngine` (which already has `stop()` handling), but `_obs_connect_thread` has no equivalent teardown.

**Fix:** Add a `closeEvent` that disconnects signals and waits for the thread:

```python
def closeEvent(self, event):
    # Tear down in-flight OBS connect thread
    if self._obs_connect_thread is not None:
        try:
            self._obs_connect_thread.connected.disconnect()
            self._obs_connect_thread.failed.disconnect()
            self._obs_connect_thread.connecting.disconnect()
        except Exception:
            pass
        self._obs_connect_thread.wait(3000)
        self._obs_connect_thread = None

    # Tear down gesture engine
    if self.engine and self.engine.isRunning():
        self.engine.stop()

    super().closeEvent(event)
```

---

## Warnings

### WR-01: `OBSController.disconnect()` Does Not Close the WebSocket

**File:** `integrations/obs_controller.py:37–39`

**Issue:** `disconnect()` sets `self.cliente = None` and `self.connected = False`, but it never calls any close/disconnect method on the underlying `obsws_python.ReqClient` object. The `ReqClient` manages a WebSocket connection internally. Dropping the Python reference without closing the socket leaves the connection open on the OBS side until it times out. This wastes a connection slot on OBS and can cause the next `OBSController.connect()` call to see the port as already connected. The `GestureEngine.run()` `finally` block at line 463 calls `self.obs.disconnect()`, relying on it to clean up.

**Fix:** Call the client's close/disconnect before nulling the reference. Check the `obsws_python` API — typically `ReqClient` has a `__exit__` or `disconnect()` or `ws.close()`:

```python
def disconnect(self):
    if self.cliente is not None:
        try:
            self.cliente.disconnect()  # or .ws.close() depending on obsws-python version
        except Exception:
            pass
        self.cliente = None
    self.connected = False
```

---

### WR-02: Race Condition — UI Thread Writes `engine.obs` Without Synchronization

**File:** `ui/main_window.py:1003–1006`

**Issue:** In `on_obs_conectado` (called from Qt main thread via signal), the code writes `self.engine.obs = obs_controller` and `self.engine.actions.obs = obs_controller` directly while `GestureEngine` is running in its own QThread. `GestureEngine._executar_acoes_gesto` runs in a `ThreadPoolExecutor` worker thread and reads `self.actions.obs`. There is no lock around these attribute writes or reads. On CPython, simple attribute assignment is GIL-protected for the assignment itself, but `ActionManager` may read `.obs` between the two writes (engine.obs set, actions.obs not yet set), creating an inconsistent state window where the engine has a new OBSController but ActionManager still holds `None` (or the old one).

Additionally, the attribute `engine.obs` is written from the main thread and read from the executor thread without any memory barrier guarantee in the Python memory model.

**Fix:** Either: (a) use a method on `GestureEngine` to atomically update both references under a lock, or (b) emit a Qt signal from the UI thread that is connected to a slot running in the engine's thread context. The minimal safe fix:

```python
# In GestureEngine, add:
def set_obs_controller(self, obs_controller):
    """Thread-safe swap of the OBS controller. Called from UI thread."""
    self.obs = obs_controller
    if self.actions:
        self.actions.obs = obs_controller

# In MainWindow.on_obs_conectado:
if self.engine and self.engine.isRunning():
    self.engine.set_obs_controller(obs_controller)
```

(This does not fully solve the race without a lock, but co-locates both writes atomically within the GIL and documents intent. A proper fix uses `QMetaObject.invokeMethod` or a Signal.)

---

### WR-03: `restart_engine()` Calls `start_engine()` Before Engine Thread Exits

**File:** `ui/main_window.py:1091–1095`

**Issue:** `restart_engine()` calls `stop_engine()` then immediately calls `start_engine()`. `stop_engine()` calls `engine.stop()` which sets `running = False` and calls `self.wait(2000)` (line 487 in `gesture_engine.py`). However, the `wait(2000)` in `GestureEngine.stop()` is called in the `GestureEngine.stop()` method context. Looking at the call: `stop_engine()` calls `self.engine.stop()`, which internally calls `self.wait(2000)` on the QThread. This *does* block — but only for 2 seconds. If the camera `encerrar()` takes longer than 2 seconds (e.g., slow DirectShow device release), the old engine thread can still be running when `start_engine()` creates a new `GestureEngine` and calls `start()`. The old engine's `camera.encerrar()` and the new engine's `camera.iniciar()` then contend for the same camera device index, causing the new camera capture to fail with "Falha ao iniciar câmera".

**Fix:** After `stop_engine()`, wait for `engine.finished` signal before calling `start_engine()`. The simplest approach:

```python
def restart_engine(self):
    if self.engine and self.engine.isRunning():
        self.engine.finished.connect(self._on_restart_after_stop)
        self.stop_engine()
    else:
        self.start_engine()

def _on_restart_after_stop(self):
    try:
        self.engine.finished.disconnect(self._on_restart_after_stop)
    except Exception:
        pass
    self.start_engine()
```

---

### WR-04: `_resumir_footer_obs` Misses the `_classificar_erro` Message for `OBSSDKError` (Senha)

**File:** `ui/main_window.py:1022`

**Issue:** `_classificar_erro` returns `"Senha incorreta — verifique as configurações do WebSocket no OBS"` for `OBSSDKError`. `_resumir_footer_obs` checks `if "Senha" in mensagem` (capital S). This works for the engine path (`update_status` strips "OBS:" prefix and passes the classified message). However, `on_obs_falhou` calls `_resumir_footer_obs(mensagem)` directly with the full classified string, where "Senha" is present — so this case works. The mismatch risk is that `_resumir_footer_obs` receives messages from two sources: (1) the `failed` signal from `OBSConnectThread` (direct classified string) and (2) the stripped substring from `update_status`. The `update_status` path strips `"OBS: "` (with a space) from `"OBS: Senha incorreta — ..."`, yielding `"Senha incorreta — ..."` — still containing "Senha". The actual mismatch is with `"recusada"` (lowercase): `_classificar_erro` returns `"Conexão recusada — ..."` and `_resumir_footer_obs` checks `if "recusada" in mensagem` (lowercase) — this matches correctly. However, when the `GestureEngine` emits `"OBS: Conexão recusada — ..."` via `status_changed`, `update_status` strips to `"Conexão recusada — ..."` and passes it to `_resumir_footer_obs`, which finds "recusada" — fine. So the actual footprint of this bug is: **the `"Timeout"` check uses a capital T** (`if "Timeout" in mensagem`), but the `_classificar_erro` return for timeout is `"Timeout — OBS não respondeu em 5s. Verifique o IP/porta"` — capital T — so it matches. The real silent failure is that **none of the checks handle the fallback message** `"Falha na conexão — verifique as configurações do WebSocket"` explicitly, so it falls through to `return "⚠️ OBS: Erro"`. This is acceptable behaviour but should be documented, as it is the default for all unknown errors and produces a non-specific footer.

The more concrete warning: `_resumir_footer_obs` is case-sensitive string matching against a human-readable localised string that could silently break if `_classificar_erro` messages are ever changed. The two functions are not co-located and share no contract.

**Fix:** Either move the footer mapping into `_classificar_erro` as a return value tuple `(detail, short)`, or replace the string matching with error-code constants:

```python
# Option: return a named tuple from _classificar_erro
ErrorInfo = namedtuple("ErrorInfo", ["detail", "short"])

def _classificar_erro(exc):
    if isinstance(exc, ConnectionRefusedError):
        return ErrorInfo("Conexão recusada — abra o OBS Studio e ative o WebSocket Server", "🔴 OBS: Offline")
    ...
```

---

## Info

### IN-01: Duplicated `gesture_cfg` Fallback Block (Dead Code + Confusion)

**File:** `engine/gesture_engine.py:363–375` and `389–398`

**Issue:** There are two blocks that construct a legacy `gesture_cfg` dict from `mapa_cenas`. The first is at lines 363–375 (runs for every frame when gesture is active). The second is at lines 387–398 (inside the cooldown check). As noted in CR-01, the second is unreachable. Removing it would reduce cyclomatic complexity and eliminate the reader confusion about which fallback applies.

**Fix:** Remove lines 387–398 entirely (the inner `if not gesture_cfg and nome_cena:` block plus its body, and also `nome_cena = self.mapa_cenas.get(gesto)` at line 387 since it becomes unused).

---

### IN-02: `_probe_opencv_camera_indexes` Redirects `sys.stderr` — Not Thread-Safe

**File:** `ui/main_window.py:220–246`

**Issue:** `_probe_opencv_camera_indexes` replaces `sys.stderr` with a `StringIO` object at line 228 to suppress OpenCV warnings during device probing. This is a process-global side-effect — if any other thread writes to `sys.stderr` during the probe loop (e.g., the logger's `StreamHandler`, the Python runtime), those messages are silently swallowed. The method is called from `__init__` (via `_populate_camera_devices` at line 557) which runs in the Qt main thread, but the risk exists during any concurrent activity. Additionally, if an exception occurs inside the loop, `sys.stderr` is only restored by the `finally` block, which is correct — but if `cv2.VideoCapture(index, cv2.CAP_DSHOW)` raises an uncaught exception type that bypasses the inner `if` checks, it could propagate past the `finally` if the exception is re-raised before the `finally` scope runs (it does not — the `finally` runs regardless in Python).

A subtler issue: if `_populate_camera_devices` is called a second time (it is called from `_load_ui_from_config` at line 766 as well as from `__init__` at line 557), the probe runs twice during `__init__`, probing all 10 camera indexes twice and holding each `VideoCapture` open for a `read()` call. On slow systems this causes a noticeable startup delay.

**Fix:** Use `os.devnull` redirect via file descriptor duplication (`os.dup2`) instead of replacing `sys.stderr`, or use `contextlib.redirect_stderr` which is both cleaner and documented. Cache the probe result:

```python
import contextlib, io

@staticmethod
def _probe_opencv_camera_indexes(max_devices=10):
    available_indexes = []
    with contextlib.redirect_stderr(io.StringIO()):
        for index in range(max_devices):
            capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if capture and capture.isOpened():
                ok, _ = capture.read()
                capture.release()
                if ok:
                    available_indexes.append(index)
    return available_indexes
```

---

_Reviewed: 2026-06-25T21:58:00-03:00_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
