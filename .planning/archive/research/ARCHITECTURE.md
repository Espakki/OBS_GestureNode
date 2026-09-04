# Architecture Patterns: OBS GestureNode v1.2

**Domain:** Desktop gesture-control app (PySide6 + OpenCV + MediaPipe)
**Researched:** 2026-06-26
**Scope:** v1.2 feature integration — low-latency camera capture + 2-hand detection

> Note: v1.1 patterns (platform abstraction, threading model, config management, platform
> layer design) are documented in the prior version of this file and are now implemented.
> This document focuses exclusively on the v1.2 integration surface.

---

## 1. Current Architecture Baseline (v1.1 implemented)

The pipeline as it runs today:

```
Physical cam (CAP_DSHOW)
  └─ CameraManager._loop_captura() [camera-capture thread, daemon]
       Condition.notify_all() on each new frame
  └─ GestureEngine.run() [QThread]
       camera.ler_frame()           ← blocks on Condition until new frame
       HandTracker.processar(frame)
         cv2.resize(→ 640×PROCESS_H, INTER_AREA)
         mp.Hands.process(frame_rgb)   max_num_hands=1
         returns (frame_small, pontos) ← pontos = flat list of 21 (px,py)
       GestureDetector.detectar(pontos)  ← returns single label or None
       _get_stable_gesture()             ← Counter-based window
       GestureStabilityMonitor.update()  ← landmark movement check
       hold_time + cooldown check
       ThreadPoolExecutor → ActionManager.executar()
       frame_ready.emit(frame_small)     ← Qt signal to main thread
```

**Key constraint already solved:** `_loop_captura` drains the camera at its own rate and
signals `ler_frame()` via `threading.Condition` — eliminates frame staleness. The residual
hardware lag floor (42–52ms for the C920) is what v1.2 features target.

---

## 2. Feature A — MSMF Backend Selection + Virtual Cam Relay

### Requirements
- CAM-05: Auto-test cv2.CAP_MSMF vs CAP_DSHOW; select lowest-lag backend
- CAM-06: If lag > threshold after backend selection, activate internal virtual cam relay
- CAM-07: Latency measured on first N frames; auto-activation, no manual config

### Integration Point: CameraManager.iniciar()

The only entry point that needs to change is `CameraManager.iniciar()` (line 40). Everything
upstream (GestureEngine, HandTracker) is unaffected.

**Current code (line 41):**
```python
self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
```

**Target logic:**
```python
def iniciar(self):
    self.capture = self._abrir_melhor_backend()   # new method
    self._configurar_propriedades()               # extract existing set() calls
    self._medir_e_decidir_modo()                  # new: measure lag, maybe activate relay
    self._iniciar_captura()                       # extract existing thread start
    # pyvirtualcam init unchanged
```

**New private method: `_abrir_melhor_backend()`**

```python
def _abrir_melhor_backend(self):
    for backend in [cv2.CAP_MSMF, cv2.CAP_DSHOW]:
        cap = cv2.VideoCapture(self.camera_index, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            self._backend_ativo = backend
            return cap
    raise RuntimeError("Nenhum backend de câmera disponível")
```

**New latency measurement in `_loop_captura()`:**

Add a measurement phase to the first N_FRAMES_MEDICAO (e.g., 10) frames. Track timestamps
to compute average frame delivery latency. Store the result in `self._lag_medido_ms`.
Once measurement is complete, set `self._medicao_concluida = True`. If
`self._lag_medido_ms > LAG_THRESHOLD_MS` (e.g., 80ms), set `self._modo_relay = True`.

**Virtual cam relay mode (CAM-06):**

When `self._modo_relay = True`, a second `cv2.VideoCapture` opens the virtual cam device
that pyvirtualcam is outputting to. The existing `_loop_captura` continues writing to
pyvirtualcam; a new `_loop_relay` thread reads from the virtual cam device and calls
`Condition.notify_all()` with relay frames. `ler_frame()` is unchanged — it still reads
from `self._ultimo_frame`.

```
Physical cam (CAP_MSMF or CAP_DSHOW)
  └─ CameraManager._loop_captura() [thread A, "camera-capture"]
       writes frame → pyvirtualcam output device
       (notify_all removed from this thread in relay mode)
  └─ CameraManager._loop_relay() [thread B, "camera-relay", NEW]
       reads from virtual cam device
       Condition.notify_all() on each relay frame
  └─ GestureEngine.run() [QThread]
       camera.ler_frame()  ← unchanged, reads self._ultimo_frame
```

**Files modified:** `core/camera.py` only.

**New attributes on CameraManager:**
- `self._backend_ativo` — which backend was selected
- `self._lag_medido_ms` — measured average latency
- `self._medicao_concluida` — flag for measurement phase completion
- `self._modo_relay` — whether virtual cam relay is active
- `self._relay_capture` — second VideoCapture for relay mode
- `self._relay_thread` — Thread for `_loop_relay`
- `self._n_frames_medicao` — configurable, default 10

**Thread safety:** `_modo_relay` is read by the main thread (for status display) and written
only once by `_loop_captura`. Use a simple `threading.Event` for `_medicao_concluida` to
allow clean waiting. The existing `threading.Condition` (`_frame_lock`) continues to
protect `_ultimo_frame` and `_frame_seq` regardless of relay mode.

**encerrar() changes:** Must also stop `_relay_thread` and release `_relay_capture` if
relay mode is active. Insert into the existing shutdown sequence before
`_captura_thread.join()`.

**GestureEngine impact:** Zero changes required. `ler_frame()` remains the only interface.

---

## 3. Feature B — 2-Hand Detection

### Requirements
- GES-01: UI toggle "1 mão" / "2 mãos" in GeralTab
- GES-02: MediaPipe max_num_hands=2 when enabled
- GES-03: Combined gesture section in GestosTab (visible when 2-hand mode active)
- GES-04: User creates combinations: left gesture + right gesture
- GES-05: Cooldown and hold_time apply to the combined gesture as a unit
- GES-06: config.json fields: `max_maos`, `combined_bindings`

### 3.1 HandTracker — Return Signature Change

**Current return (line 53):**
```python
return frame_small, pontos   # pontos = flat list of 21 (px, py) tuples, or []
```

**New return:**
```python
return frame_small, maos
# maos = list of dicts, one per detected hand, in detection order:
# [{"handedness": "Left", "landmarks": [(px, py), ...]}, ...]
# Empty list when no hands detected.
```

**New constructor parameter:** `max_num_maos: int = 1` (default preserves backward
compatibility for code that hasn't been updated yet, but GestureEngine will always
pass the config value).

**GESTURE_ALIASES normalization note:** handedness labels from MediaPipe are "Left" and
"Right" (capital first letter, English). These are camera-mirrored: MediaPipe's "Left"
appears on the right side of the preview because `cv2.flip(frame, 1)` mirrors horizontally.
Document this as a constant comment in `hand_tracker.py`.

**Files modified:** `core/hand_tracker.py` only.

**Backward compatibility:** GestureEngine is updated in the same phase — no callers use the
old return signature that won't be updated. There are no other callers of `HandTracker.processar()`.

### 3.2 GestureDetector — Combined Gesture Method

`detectar()` stays unchanged. Add one new method:

```python
def detectar_par(self, pontos_esq, pontos_dir):
    """Classifica par de gestos e retorna chave combinada.

    Args:
        pontos_esq: list of 21 (px, py) for the left hand, or None
        pontos_dir: list of 21 (px, py) for the right hand, or None
    Returns:
        str: combined key "GESTO_ESQ+GESTO_DIR", or None if either hand missing/unclassified
    """
    if not pontos_esq or not pontos_dir:
        return None
    gesto_esq = self.detectar(pontos_esq)
    gesto_dir = self.detectar(pontos_dir)
    if gesto_esq is None or gesto_dir is None:
        return None
    return f"{gesto_esq}+{gesto_dir}"
```

Combined key format: `"GESTO_ESQ+GESTO_DIR"` (e.g., `"THUMBS_UP+FIST"`). Both parts use
the canonical internal name (post-GESTURE_ALIASES normalization).

**GESTURE_ALIASES for combined keys:** `_normalize_gesture_keys()` in GestureEngine must
also normalize `combined_bindings` keys. Each part of the composite key is normalized
independently by splitting on `+`, normalizing each part, and rejoining.

**Files modified:** `core/gesture_detector.py` only.

### 3.3 GestureEngine — 2-Hand Pipeline Integration

This is the largest change. GestureEngine.run() currently assumes one hand. The 2-hand path
is additive (not a replacement): when `max_maos == 1`, code path is unchanged.

**New attributes in `_setup()`:**
```python
self.max_maos = int(gestures_cfg.get("max_maos", 1))
self._combined_bindings_lock = threading.RLock()   # same pattern as _bindings_lock
self._combined_bindings = {}                        # keyed by "GESTO_ESQ+GESTO_DIR"
self._combined_bindings = gestures_cfg.get("combined_bindings", {})

# Second stability monitor for 2-hand mode
if self.max_maos == 2:
    self.stability_monitor_esq = GestureStabilityMonitor(...)
    self.stability_monitor_dir = GestureStabilityMonitor(...)
    # stability_monitor (existing) still used for 1-hand fallback
```

**HandTracker construction change in `_setup()`:**
```python
self.tracker = HandTracker(max_num_maos=self.max_maos)  # was: HandTracker()
```

**New property + setter (same pattern as gesture_bindings):**
```python
@property
def combined_bindings(self): ...

@combined_bindings.setter
def combined_bindings(self, value): ...
```

**`_normalize_gesture_keys()` extension:**
```python
# Existing: normalizes self._gesture_bindings and self._mapa_cenas
# Add: normalizes self._combined_bindings
with self._combined_bindings_lock:
    if isinstance(self._combined_bindings, dict):
        normalized = {}
        for key, val in self._combined_bindings.items():
            parts = key.split("+", 1)
            if len(parts) == 2:
                n_key = "+".join([
                    self._normalize_gesture_name(parts[0]),
                    self._normalize_gesture_name(parts[1])
                ])
                normalized[n_key] = val
            else:
                normalized[key] = val
        self._combined_bindings = normalized
```

**run() loop changes for 2-hand mode:**

```python
frame, maos = self.tracker.processar(frame, draw_skeleton=self.show_skeleton)

if self.max_maos == 1:
    # --- EXISTING 1-HAND PATH (refactored to use maos) ---
    pontos = maos[0]["landmarks"] if maos else []
    raw_gesture = self.detector.detectar(pontos) if pontos else None
    # ... rest of existing logic unchanged (variable names preserved) ...

elif self.max_maos == 2:
    # --- NEW 2-HAND PATH ---
    mao_esq = next((m for m in maos if m["handedness"] == "Left"), None)
    mao_dir = next((m for m in maos if m["handedness"] == "Right"), None)

    pontos_esq = mao_esq["landmarks"] if mao_esq else None
    pontos_dir = mao_dir["landmarks"] if mao_dir else None

    raw_combined = self.detector.detectar_par(pontos_esq, pontos_dir)
    raw_combined = self._normalize_combined_key(raw_combined)   # new method
    gesto_combinado = self._get_stable_gesture(raw_combined)    # reuses existing window

    # Stability: both hands must be stable
    esq_stable = self.stability_monitor_esq.update(pontos_esq) if pontos_esq else False
    dir_stable = self.stability_monitor_dir.update(pontos_dir) if pontos_dir else False
    is_stable = esq_stable and dir_stable

    # Hold/cooldown/action dispatch: same logic as 1-hand but key = gesto_combinado
    # and bindings read from combined_bindings dict
    # ...
```

**`_get_stable_gesture()` reuse:** The same Counter-window method works for combined keys
because the key is just a string (`"THUMBS_UP+FIST"`). No changes needed.

**Files modified:** `engine/gesture_engine.py` only.

**main_window.py wiring:** Two new paths needed:
1. `_on_hand_mode_changed()` — saves `max_maos` to config, calls `restart_engine()`
   (engine must restart because HandTracker is constructed in `_setup()`)
2. `_save_combined_binding()` / `_load_combined_bindings_ui()` — reads/writes
   `config["gestures"]["combined_bindings"]`
3. Live-update path: `engine.combined_bindings = ...` when combined bindings change
   (same pattern as line 750: `self.engine.gesture_bindings = ...`)

**Files modified:** `ui/main_window.py`.

### 3.4 Config Schema Changes

New fields in `config.json`:
```json
{
  "camera": {
    "backend_mode": "auto",
    "lag_threshold_ms": 80
  },
  "gestures": {
    "max_maos": 1,
    "combined_bindings": {
      "THUMBS_UP+FIST": {
        "enabled": true,
        "hold_time": 2.0,
        "cooldown": 2.0,
        "scene": "",
        "sound_file": "",
        "hotkey": "",
        "use_scene": false,
        "use_sound": false,
        "use_hotkey": false
      }
    }
  }
}
```

`backend_mode` values: `"auto"` (try MSMF then DSHOW then relay), `"msmf"`, `"dshow"`,
`"relay"`. Defaults to `"auto"`.

`lag_threshold_ms`: threshold for auto-activating relay mode. Default 80ms.

**Files modified:** `config.json` (schema only; GestureEngine._setup() reads new fields).

### 3.5 GeralTab — Hand Count Toggle

Add a new toggle row below the FPS row, identical pattern to `mode_group` (QButtonGroup,
QPushButton with `setCheckable(True)`):

```python
self.maos_group = QButtonGroup(self)
self.maos_1_button = QPushButton("1 mão")
self.maos_2_button = QPushButton("2 mãos")
# ... same pattern as mode_group ...
camera_form.addRow("Detecção:", maos_row)
```

Add `set_maos(n: int)` method analogous to `set_mode()`.

**Files modified:** `ui/tabs/geral_tab.py`.

### 3.6 GestosTab — Combined Gesture Section

A new section below the existing single-hand gesture grid. Visible only when
`max_maos == 2`. Structure:

```
[title: "Gestos Combinados (2 mãos)"]
[list of configured combinations — each is a collapsible card]
  [card] THUMBS_UP + FIST  [trash icon]
         ... same action editor as single-hand ...
[+ Adicionar combinação]  [QPushButton, opens picker dialog]
```

The picker dialog (`CombinedGestureDialog`) shows two QComboBoxes populated with the
canonical gesture names from `GESTURE_ALIASES` (same list as the existing gesture buttons),
one for each hand.

**New widget:** `CombinedGestureDialog` (new class in `ui/tabs/gestos_tab.py` or
`ui/dialogs/combined_gesture_dialog.py`). Simpler to keep in `gestos_tab.py` for v1.2.

**Visibility toggling:** `GestosTab.set_maos_mode(n: int)` shows/hides the combined section
container. Called from `MainWindow._on_hand_mode_changed()`.

**Files modified:** `ui/tabs/gestos_tab.py`, possibly `ui/main_window.py`.

---

## 4. Component Modification Map

| File | Status | What Changes |
|------|--------|--------------|
| `core/camera.py` | MODIFIED | `iniciar()` backend selection; latency measurement in `_loop_captura`; new `_loop_relay` thread; `encerrar()` relay shutdown |
| `core/hand_tracker.py` | MODIFIED | `max_num_maos` constructor param; return signature → list of dicts with handedness |
| `core/gesture_detector.py` | MODIFIED | Add `detectar_par()` method (existing `detectar()` unchanged) |
| `engine/gesture_engine.py` | MODIFIED | `_setup()` reads `max_maos` and `combined_bindings`; constructs HandTracker with `max_num_maos`; run() 2-hand path; second stability monitors; `_normalize_gesture_keys()` extended; `combined_bindings` property |
| `ui/tabs/geral_tab.py` | MODIFIED | Add hand count toggle row |
| `ui/tabs/gestos_tab.py` | MODIFIED | Add combined gesture section + `CombinedGestureDialog` |
| `ui/main_window.py` | MODIFIED | Wire hand mode toggle; load/save `combined_bindings`; live-update `engine.combined_bindings` |
| `config.json` | MODIFIED | New fields: `camera.backend_mode`, `camera.lag_threshold_ms`, `gestures.max_maos`, `gestures.combined_bindings` |

**No new files required.** All changes extend existing modules.

---

## 5. Data Flow Changes

### Before (v1.1):
```
ler_frame() → (ok, frame)
processar(frame) → (frame_small, pontos)     ← pontos: list[tuple]
detectar(pontos) → str|None
```

### After (v1.2, 1-hand mode):
```
ler_frame() → (ok, frame)                   ← unchanged
processar(frame) → (frame_small, maos)       ← maos: list[{"handedness", "landmarks"}]
maos[0]["landmarks"] → pontos
detectar(pontos) → str|None                  ← unchanged
```

### After (v1.2, 2-hand mode):
```
ler_frame() → (ok, frame)
processar(frame) → (frame_small, maos)       ← up to 2 dicts
detectar_par(pontos_esq, pontos_dir) → "GESTO_ESQ+GESTO_DIR"|None
_get_stable_gesture(raw_combined) → str|None ← reused unchanged
combined_bindings[gesto_combinado] → action config
```

---

## 6. Build Order and Dependency Rationale

### Phase 1 — Camera Backend Selection (CAM-05) [foundation, no dependencies]
**Scope:** `core/camera.py` — `iniciar()` + `_abrir_melhor_backend()`
**Why first:** Standalone change. No HandTracker or UI impact. Provides the backend
selection foundation that CAM-06/07 depend on. Short and testable in isolation.

### Phase 2 — Latency Measurement + Virtual Cam Relay (CAM-06, CAM-07)
**Scope:** `core/camera.py` — latency logic in `_loop_captura`, `_loop_relay`, `encerrar()`
**Why after Phase 1:** Relay mode requires a stable backend selection. The latency
measurement gate (`_medicao_concluida`) decides whether to activate relay.
**Dependency:** Phase 1 must be committed and tested before adding relay complexity.

### Phase 3 — HandTracker 2-Hand Return Signature (GES-02 baseline)
**Scope:** `core/hand_tracker.py` + corresponding update in `engine/gesture_engine.py`
**Why independent:** Touches a completely different code path from Phases 1-2. Can be done
in parallel with Phases 1-2 or after.
**Critical:** `gesture_engine.py` must be updated in the same commit as `hand_tracker.py` —
the return signature change breaks `frame, pontos = self.tracker.processar(...)` and will
cause a runtime `ValueError` if both files are not updated atomically.
**1-hand backward compatibility:** After this phase, 1-hand mode must still work identically.
Verify by running existing gesture detection smoke test.

### Phase 4 — Combined Gesture Detection + Config Schema (GES-02, GES-04, GES-05, GES-06)
**Scope:** `core/gesture_detector.py` + `engine/gesture_engine.py` (2-hand pipeline) + `config.json`
**Why after Phase 3:** Requires `HandTracker.processar()` to return handedness dicts.
`detectar_par()` can be added to `GestureDetector` independently, but `GestureEngine` can't
use it until HandTracker provides separate per-hand landmarks.
**Stability monitors:** Add `stability_monitor_esq` and `stability_monitor_dir` in the same
phase. `GestureStabilityMonitor` class itself is unchanged.

### Phase 5 — UI (GES-01, GES-03, GES-04 UI)
**Scope:** `ui/tabs/geral_tab.py`, `ui/tabs/gestos_tab.py`, `ui/main_window.py`
**Why last:** UI wires onto engine features that must exist first. The hand count toggle
triggers `restart_engine()` — engine must already support `max_num_maos` before the UI
can meaningfully change it. The combined gesture editor reads/writes `combined_bindings`
from config — the config schema must already be defined.

### Dependency Graph:
```
Phase 1 (cam backend) ──→ Phase 2 (cam relay)
                                        \
Phase 3 (handtracker sig) ──→ Phase 4 (2-hand engine) ──→ Phase 5 (UI)
```

Phases 1/2 and Phase 3/4/5 are two independent tracks that can be planned in parallel
but Phase 1 should complete before Phase 2, and Phase 3 before Phase 4 before Phase 5.

---

## 7. Thread Safety Implications

### CameraManager relay mode
- `_modo_relay: bool` — written once by `_loop_captura` (after measurement), read by
  `_loop_relay` and potentially by main thread for status. Use `threading.Event` or
  a simple boolean guarded by `_frame_lock` to avoid a separate lock.
- `_relay_capture` — accessed only by `_loop_relay`. No lock needed.
- `_relay_thread` — lifecycle managed by `iniciar()` and `encerrar()` on the Qt main
  thread. Must check if relay mode is active before joining.
- Do NOT access `_relay_capture.read()` or `.release()` from two threads.

### HandTracker processar()
- Called exclusively from `GestureEngine.run()` (engine QThread). No shared state change.
  The `mp.solutions.hands.Hands` object is not thread-safe — maintaining single-thread
  access is already the pattern and must not change.

### GestureEngine combined_bindings
- Same `_bindings_lock` (RLock) pattern as `gesture_bindings`. Use the same property
  getter/setter idiom. `main_window.py` sets `engine.combined_bindings = ...` on the
  main thread; `run()` reads it on the engine thread.
- Consider combining both locks into one to avoid lock-ordering issues, or ensure
  consistent acquisition order if both locks are ever held simultaneously.

### GestureStabilityMonitor (2 instances)
- `stability_monitor_esq` and `stability_monitor_dir` are only accessed from
  `GestureEngine.run()`. No shared access. No lock needed.

### engine.max_maos
- Set once in `_setup()` before `run()` is called. Read-only during `run()`. No lock needed.
- Changing `max_maos` requires `restart_engine()` — which creates a new `GestureEngine`
  instance calling `_setup()` again. No live reconfiguration of this field.

---

## 8. Anti-Patterns to Avoid

### Relay mode: opening same physical device in two threads
The physical camera is opened by `_loop_captura`. `_loop_relay` opens the virtual camera
device — a different device index. Never open the same `cv2.VideoCapture` from two threads.
If relay mode is activated, Thread A writes to pyvirtualcam; Thread B reads from virtual
device. Thread A does NOT call `Condition.notify_all()` in relay mode (Thread B does).

### Changing HandTracker return type without atomic commit to gesture_engine.py
The line `frame, pontos = self.tracker.processar(...)` in `gesture_engine.py` will throw
`ValueError: not enough values to unpack` if HandTracker starts returning 3 values or a
different structure. Both files must change in one commit.

### Sending `maos[0]["landmarks"]` without None-check in 1-hand mode
When `max_maos == 1` but no hand is detected, `maos` is an empty list. `maos[0]` raises
`IndexError`. Always guard: `pontos = maos[0]["landmarks"] if maos else []`.

### Combined key normalization order
`_normalize_gesture_keys()` must normalize `combined_bindings` AFTER normalizing both
`gesture_bindings` and `mapa_cenas`. The normalization rewrites dict keys atomically —
running it on `combined_bindings` before the component names are themselves normalized
could produce inconsistent states if called in the wrong order.

### Hardcoding "Left"/"Right" in combined binding keys
User-facing config uses the canonical gesture names, not the handedness labels. The
combined key format is `"GESTO_ESQ+GESTO_DIR"` where GESTO_ESQ is what the LEFT hand
shows (camera-mirrored from MediaPipe's perspective). Expose this as left/right in the UI
clearly to avoid user confusion.

---

## 9. Sources and Confidence

| Area | Confidence | Basis |
|------|------------|-------|
| CameraManager integration point | HIGH | Directly read `core/camera.py` source |
| HandTracker return signature | HIGH | Directly read `core/hand_tracker.py` source |
| GestureEngine run() structure | HIGH | Directly read `engine/gesture_engine.py` source |
| GestureEngine threading patterns | HIGH | Directly read RLock/property pattern |
| main_window.py wiring patterns | HIGH | Directly read engine.gesture_bindings assignment sites |
| MediaPipe handedness label values | MEDIUM | Training knowledge (mediapipe 0.10.14 `multi_handedness` returns "Left"/"Right" strings) — verify in smoke test |
| pyvirtualcam relay on Windows | MEDIUM | Training knowledge; pyvirtualcam on Windows uses OBS VirtualCam or similar DirectShow virtual device — relay read requires that device to be visible as a VideoCapture index |
| lag_threshold_ms value (80ms) | LOW | Heuristic; 42–52ms is hardware floor per debug notes, 80ms gives headroom for MSMF to be "good enough" |
