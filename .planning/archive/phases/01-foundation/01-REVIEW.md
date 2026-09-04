---
phase: 01-foundation
reviewed: 2026-06-23T19:46:00-03:00
depth: standard
files_reviewed: 4
files_reviewed_list:
  - core/gesture_aliases.py
  - core/gesture_detector.py
  - engine/gesture_engine.py
  - ui/main_window.py
findings:
  critical: 3
  warning: 3
  info: 1
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-23T19:46:00-03:00
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 1 delivered five targeted fixes: dependency pinning, config cleanup, GESTURE_ALIASES consolidation, RLock protection on GestureEngine, and atomic config save with debounce. The structural changes are sound — the module hierarchy is clean, the atomic write pattern is correct, and the RLock acquisition strategy is well-reasoned.

However, the GESTURE_ALIASES consolidation (01-03) introduced a silent data mismatch: three gesture display names in `ALL_GESTURES` do not match the values produced by the alias translation layer, permanently breaking those gesture bindings. Additionally, the `restart_engine` flow contains a race that causes the `on_engine_finished` signal from the dying engine to null out the freshly created replacement engine. The `_do_save_config` exception narrowing silently swallows serialization errors.

---

## Critical Issues

### CR-01: GESTURE_ALIASES values do not match ALL_GESTURES keys — ROCK, TRES, QUATRO gestures are permanently broken

**File:** `core/gesture_aliases.py:10-12` / `ui/main_window.py:73-75`

**Issue:** The canonical alias lookup chain is: detector returns internal code → `_normalize_gesture_name()` maps via `GESTURE_ALIASES` → result is compared against `ALL_GESTURES` display names and config binding keys. Three aliases produce values that have no matching entry in `ALL_GESTURES`:

| Detector output | GESTURE_ALIASES value | ALL_GESTURES key | Match? |
|---|---|---|---|
| `"ROCK"` | `"ROCK"` | `"Rock"` | No — case differs |
| `"THREE"` | `"TRES"` | `"Três"` | No — encoding differs |
| `"FOUR"` | `"QUATRO"` | `"Quatro"` | No — case differs |

Consequence: when the engine calls `self.gesture_bindings.get(gesto, {})`, the key `"ROCK"` / `"TRES"` / `"QUATRO"` is looked up in a bindings dict whose keys were normalized in `_init_config_schema` from `ALL_GESTURES` names (`"Rock"`, `"Três"`, `"Quatro"`). The lookup always returns `{}`, so the `if not gesture_cfg.get("enabled", True): continue` branch skips the gesture. These three gestures can never fire any action regardless of user configuration.

**Fix:** Align `GESTURE_ALIASES` values with the display names used in `ALL_GESTURES`:

```python
# core/gesture_aliases.py
GESTURE_ALIASES = {
    "THUMBS_UP":   "Joinha",
    "THUMBS_DOWN": "Deslike",
    "OPEN_HAND":   "Mão aberta",
    "FIST":        "Punho",
    "POINT":       "Apontando p/ cima",
    "ROCK":        "Rock",       # was "ROCK"
    "THREE":       "Três",       # was "TRES"
    "FOUR":        "Quatro",     # was "QUATRO"
    "OK_SIGN":     "OK",
    "CALL_ME":     "Me liga",
    "V":           "V",
    "Escoteiro":   "Escoteiro",
    "Dedo do Meio": "Dedo do Meio",
    "Arminha":     "Arminha",
}
```

---

### CR-02: restart_engine race — on_engine_finished from dying engine nulls out the newly created engine

**File:** `ui/main_window.py:1045-1049` / `ui/main_window.py:1113-1120`

**Issue:** `restart_engine` calls `stop_engine()` then immediately `start_engine()`. `stop_engine()` (line 1037) connects `self.engine.finished` to `on_engine_finished`, then calls `engine.stop()` which sets `running=False` and calls `self.wait(2000)` (blocking up to 2 s for the thread to exit). After `stop_engine()` returns, `start_engine()` creates a new `GestureEngine` and assigns it to `self.engine`. However, the `finished` signal is still connected on the **old** engine object. When that old thread eventually emits `finished`, Qt dispatches it to `on_engine_finished`, which executes `self.engine = None` (line 1119) — clobbering the new engine reference. The new engine continues running (camera thread is live), but `self.engine` is `None`, so `stop_engine()` becomes a no-op and the engine can never be stopped again without restarting the app.

The 2-second `wait()` in `GestureEngine.stop()` makes this race narrow but reliably reproducible when the camera loop takes longer than 2 s to exit (which can happen during OBS disconnect).

**Fix:** Clear the old engine's `finished` connection before creating the new one, or disconnect it in `stop_engine` after `stop()` returns:

```python
def restart_engine(self):
    old_engine = self.engine
    running = bool(old_engine and old_engine.isRunning())
    if running:
        # Disconnect on_engine_finished from old engine before replacement
        try:
            old_engine.finished.disconnect(self.on_engine_finished)
        except Exception:
            pass
        old_engine.stop()
        # engine ref intentionally kept until thread fully exits; do not assign None here
    self.engine = None  # break the reference so start_engine builds fresh
    self.start_engine()
```

Alternatively, check inside `on_engine_finished` whether the emitting object is still the current engine before nulling the reference:

```python
def on_engine_finished(self):
    if self.sender() is not self.engine:
        return  # stale signal from replaced engine — ignore
    self.set_config_enabled(True)
    ...
    self.engine = None
```

---

### CR-03: _do_save_config silently drops config on non-OSError exceptions (e.g. json.TypeError)

**File:** `ui/main_window.py:1146-1160`

**Issue:** The outer `except` clause catches only `OSError`. The inner `try` block calls `json.dump(self.config, ...)`, which raises `TypeError` when any value in `self.config` is not JSON-serializable (e.g. a `Path` object, a Qt widget accidentally stored in config, or a `None` that becomes a non-serializable type). A `TypeError` from `json.dump` propagates past the inner `except Exception` (which re-raises), is not caught by `except OSError`, and surfaces as an unhandled exception in a Qt timer callback — Qt swallows it silently on Windows. The tempfile cleanup runs correctly, but the save is lost with no log entry and no user notification.

```python
# Current — only OSError is caught at the outer level
except OSError as exc:
    logger.error("Falha ao salvar configuracao: %s", exc)
```

**Fix:** Broaden the outer catch to `Exception` so serialization errors are also logged:

```python
except Exception as exc:
    logger.error("Falha ao salvar configuracao: %s", exc)
```

If distinguishing error types is needed, keep both:

```python
except TypeError as exc:
    logger.error("Configuracao contem valor nao serializavel: %s", exc)
except OSError as exc:
    logger.error("Falha de I/O ao salvar configuracao: %s", exc)
```

---

## Warnings

### WR-01: Dead code — gesture_cfg fallback block at lines 383-392 is unreachable

**File:** `engine/gesture_engine.py:383-392`

**Issue:** Inside the `if inicio_gesto and (tempo_atual - inicio_gesto) >= hold_time and is_stable:` block (line 378), the code checks `if not gesture_cfg and nome_cena:` at line 383 and builds a legacy fallback dict. But `gesture_cfg` was already guaranteed to be non-empty at this point: the identical fallback was applied at lines 358-369, and if `gesture_cfg` remained `{}` after that block (because there was no legacy scene either), line 371 would have executed `continue` (since `{}.get("enabled", True)` is `True`, actually that does not skip — wait: an empty dict's `.get("enabled", True)` is `True` so it does NOT skip). But by line 383, `nome_cena = self.mapa_cenas.get(gesto)` is evaluated, and at line 358-369 the same `mapa_cenas.get(gesto, "")` was already used to populate `gesture_cfg`. So if `nome_cena_legado` had a value at line 359, `gesture_cfg` is now non-empty, making line 383 `if not gesture_cfg` always False. If `nome_cena_legado` was empty, `nome_cena` at line 381 is equally empty, so line 383 is `if not {} and None` = `if True and False` = False. The block at 383-392 is dead in all paths.

**Fix:** Remove the redundant block at lines 380-392:

```python
# Remove lines 380-392; the fallback was already applied at lines 358-369.
# The block starting at line 394 can reference gesture_cfg directly.
if self.actions and gesture_cfg:
    ...
```

---

### WR-02: _normalize_gesture_keys called from Qt main thread on a running QThread without synchronization contract

**File:** `ui/main_window.py:889` and `ui/main_window.py:915`

**Issue:** `on_current_gesture_changed` (line 889) and `on_dynamic_setting_changed` (line 915) call `self.engine._normalize_gesture_keys()` directly from the Qt main thread while `GestureEngine` is running in its own QThread. Although `_normalize_gesture_keys` acquires `_bindings_lock` internally (line 264), the caller has already set `self.engine.gesture_bindings` and `self.engine.mapa_cenas` via their property setters (each of which also acquire the lock) in the two preceding lines. The three lock acquisitions are not atomic as a unit: between the two property sets and the normalize call, the engine thread can read a partially-updated state where `_gesture_bindings` is updated but `_mapa_cenas` is not yet (or vice versa).

Additionally, calling a private method of a QThread from an external thread is a design violation that bypasses the intended signal/slot decoupling.

**Fix:** Make the update atomic by adding a dedicated method on `GestureEngine` that updates both dicts and normalizes under a single lock acquisition, callable via `QMetaObject.invokeMethod` or a Qt signal:

```python
# In GestureEngine
def update_bindings(self, bindings, mapa_cenas):
    with self._bindings_lock:
        self._gesture_bindings = bindings or {}
        self._mapa_cenas = mapa_cenas or {}
        self._normalize_gesture_keys_locked()  # operates under already-held lock
```

---

### WR-03: stability_monitor.update() called with pontos=None when no hand is detected

**File:** `engine/gesture_engine.py:354-355`

**Issue:** `pontos` is the return value of `self.tracker.processar(frame, ...)`. When no hand is detected, `HandTracker.processar` returns `None` or an empty list for landmarks. `self.detector.detectar(pontos)` handles `None`/non-21-length by returning `None` (line 24-25 of `gesture_detector.py`). In that case `raw_gesture` is `None`, `gesto` from `_get_stable_gesture` is `None`, and the `if gesto:` block is skipped — so `stability_monitor.update(pontos)` is never reached with `None`. This is safe.

However, when `gesto` IS truthy, `pontos` could theoretically be a list of fewer than 21 points (the detector returned `None` earlier but the stability window still has a non-None majority gesture from prior frames). In that state `stability_monitor.update(pontos)` is called, and `_calculate_average_movement` handles length mismatches by returning `float('inf')` — so stability is never satisfied and no false trigger occurs. This is functionally safe but the code comment says "Atualizar monitor com landmarks atuais" without acknowledging this edge case, and reliance on `float('inf')` as a sentinel is fragile if the threshold comparison ever changes.

**Fix:** Add an explicit guard before calling the stability monitor:

```python
if self.stability_enabled and pontos and len(pontos) == 21:
    is_stable = self.stability_monitor.update(pontos)
```

---

## Info

### IN-01: GESTURE_ALIASES contains inconsistent key naming conventions — mixed UPPER_SNAKE_CASE and display strings

**File:** `core/gesture_aliases.py:16-19`

**Issue:** The module comment says keys are "código interno do detector" (internal detector code). Most keys follow `UPPER_SNAKE_CASE` (`THUMBS_UP`, `ROCK`, `OK_SIGN`), but four keys are display strings with mixed case and spaces: `"V"`, `"Escoteiro"`, `"Dedo do Meio"`, `"Arminha"`. This is because the detector returns these exact strings. The inconsistency is not a bug (the detector must return what it returns), but it makes the module contract ambiguous — a future developer may normalize a new detector output to `UPPER_SNAKE_CASE` before checking aliases, causing a miss.

**Fix:** Add a code comment explicitly documenting why these four keys deviate from the convention:

```python
# Passthrough gestures: o detector já retorna o nome de exibição diretamente.
# NÃO normalizar para UPPER_SNAKE_CASE — a chave deve ser idêntica ao retorno do detector.
"V":            "V",
"Escoteiro":    "Escoteiro",
"Dedo do Meio": "Dedo do Meio",
"Arminha":      "Arminha",
```

---

_Reviewed: 2026-06-23T19:46:00-03:00_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
