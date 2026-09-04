---
phase: 03-obs-connection
fixed_at: 2026-06-25T22:10:00-03:00
review_path: .planning/phases/03-obs-connection/03-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-06-25T22:10:00-03:00
**Source review:** .planning/phases/03-obs-connection/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (3 Critical + 4 Warning; Info excluded per fix_scope=critical_warning)
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Dead Legacy Fallback Inside `_connect_obs` Guard — Action Never Fires for Legacy Gestures

**Files modified:** `engine/gesture_engine.py`
**Commit:** e15f2e9
**Applied fix:** Removed the second duplicate `gesture_cfg` fallback block (lines 387–398 in the original) that was unreachable dead code. Also removed the unused `nome_cena = self.mapa_cenas.get(gesto)` variable that preceded it. The first fallback at lines 363–375 is sufficient; the `if self.actions and gesture_cfg:` dispatch block now follows the cooldown check directly.

---

### CR-02: `OBSController` Instance Leaked When `testar_conexao_obs` Is Called Rapidly

**Files modified:** `ui/main_window.py`
**Commit:** c5a6500
**Applied fix:** Added a guard at the top of `testar_conexao_obs` that disconnects all signals (`connected`, `failed`, `connecting`) from any in-flight `OBSConnectThread` before overwriting `self._obs_connect_thread`. Stale signals from the previous thread are now silently dropped instead of firing on the new connection state.

---

### CR-03: No `closeEvent` — `OBSConnectThread` Can Run Past Window Destruction

**Files modified:** `ui/main_window.py`
**Commit:** c9f4b24
**Applied fix:** Added `closeEvent(self, event)` override to `MainWindow`. It disconnects all signals from `_obs_connect_thread`, waits up to 3 seconds for the thread to finish, and calls `engine.stop()` if the gesture engine is running. Calls `super().closeEvent(event)` at the end to ensure normal Qt close processing.

---

### WR-01: `OBSController.disconnect()` Does Not Close the WebSocket

**Files modified:** `integrations/obs_controller.py`
**Commit:** 2e2acf0
**Applied fix:** `disconnect()` now calls `self.cliente.disconnect()` (confirmed present on `obsws_python.ReqClient` via API inspection) inside a `try/except` before nulling the reference. This lets the underlying WebSocket close cleanly on the OBS side.

---

### WR-02: Race Condition — UI Thread Writes `engine.obs` Without Synchronization

**Files modified:** `engine/gesture_engine.py`, `ui/main_window.py`
**Commit:** e8bc25a
**Applied fix:** Added `set_obs_controller(self, obs_controller)` method to `GestureEngine` that performs both attribute writes (`self.obs` and `self.actions.obs`) in one call, co-locating them within the GIL. Updated `MainWindow.on_obs_conectado` to call `self.engine.set_obs_controller(obs_controller)` instead of writing the two attributes separately from the UI thread.

---

### WR-03: `restart_engine()` Calls `start_engine()` Before Engine Thread Exits

**Files modified:** `ui/main_window.py`
**Commit:** 0384d54
**Applied fix:** `restart_engine()` now connects `engine.finished` to a new `_on_reiniciar_apos_parada` slot before calling `stop_engine()`. The slot disconnects itself and calls `start_engine()` only after the engine thread has fully exited. If the engine is not running, `start_engine()` is called immediately.

---

### WR-04: `_resumir_footer_obs` Misses the `_classificar_erro` Message (Fragile String Matching)

**Files modified:** `integrations/obs_connect_thread.py`, `ui/main_window.py`
**Commit:** 25c526e
**Applied fix:** Added `_MSGS_OBS` dict and `_resumir_footer_obs(mensagem)` function to `obs_connect_thread.py`, co-located with `_classificar_erro`. The keys in `_MSGS_OBS` match the exact substrings used by `_classificar_erro` return values, so any future change to those messages will require updating both in the same file. `main_window.py` imports the new function (aliased as `_resumir_footer_obs_fn`) and delegates from the `_resumir_footer_obs` method, replacing the nine-line inline string-matching chain.

---

_Fixed: 2026-06-25T22:10:00-03:00_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
