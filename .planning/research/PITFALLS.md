# Pitfalls Research

**Domain:** Real-time gesture detection desktop app — adding MSMF backend, internal virtual camera loop, and 2-hand MediaPipe detection to an existing OpenCV + MediaPipe + pyvirtualcam Windows app
**Researched:** 2026-06-26
**Confidence:** HIGH — derived from direct codebase inspection of `core/camera.py`, `core/hand_tracker.py`, `core/gesture_detector.py`, `engine/gesture_engine.py`, `config.json`, and the two feature TODO specs.

---

## Critical Pitfalls

Mistakes in this category cause silent misbehavior or guaranteed regressions in the existing system.

---

### CRITICAL-01: HandTracker Flat Landmark List Breaks GestureDetector With 2 Hands

**What goes wrong:**
Enabling `max_num_hands=2` in `HandTracker.__init__()` without changing `processar()` causes ALL gesture detection — including existing single-hand gestures — to silently return `None` whenever both hands are visible. `processar()` concatenates all landmarks from all detected hands into a single flat list. With 1 hand: 21 points (works). With 2 hands: 42 points. `GestureDetector.detectar()` has `if len(pontos) != 21: return None`, so it unconditionally rejects 42-point input. The user sees both hand skeletons drawn correctly on the preview but no gestures fire at all. It looks like a detection regression.

**Why it happens:**
The original `HandTracker` API was designed for a single hand. `processar()` iterates `resultado.multi_hand_landmarks` and appends all points from all hands into one list, making the return value structurally incompatible with multi-hand callers. Changing `max_num_hands` in the `Hands()` constructor is not enough — it only controls how many hands MediaPipe tracks internally. The caller contract must also change.

**How to avoid:**
Refactor `HandTracker.processar()` to return a list of per-hand landmark sets — `List[List[Tuple[int,int]]]` — instead of a flat `List[Tuple[int,int]]`. `GestureDetector.detectar()` receives one hand's 21 points and stays unchanged. The engine calls `detectar()` once per detected hand. Combined gesture detection is an explicit separate code path that receives two per-hand results, not a flat merged list.

**Warning signs:**
- Gestures never fire when 2 hands are visible, but fire normally when one hand is hidden from camera
- No error or exception raised — detection silently returns `None`
- Adding `print(len(pontos))` shows 42 when both hands are in frame

**Phase to address:**
First task of the 2-hand detection phase. This is a prerequisite for all other 2-hand work — nothing else should be built until per-hand landmark lists are the API contract.

---

### CRITICAL-02: GestureStabilityMonitor Breaks When Hand Count Fluctuates

**What goes wrong:**
`GestureStabilityMonitor.update()` stores `previous_landmarks` and compares it to the current frame's landmarks. `_calculate_average_movement()` returns `float('inf')` when `len(prev_landmarks) != len(curr_landmarks)`. In 2-hand mode, when a hand enters or leaves the frame, the landmark count changes between consecutive frames (21 → 42 or 42 → 21). The monitor returns `float('inf')` movement, the `stable_frame_count` resets to 0, and `is_stable` stays `False` indefinitely while hand count is in flux. The engine produces a valid gesture label from the detection window but the stability gate permanently blocks it from firing.

**Why it happens:**
The monitor was built assuming a fixed count of 21 landmarks. The `_calculate_average_movement()` guard for mismatched lengths (`return float('inf')`) was defensive code for error cases; it becomes the normal execution path when hand count changes between frames — which is a routine event whenever a hand partially enters or exits the camera frame.

**How to avoid:**
After refactoring `HandTracker` to return per-hand landmark lists (CRITICAL-01), give each tracked hand its own `GestureStabilityMonitor` instance. The engine tracks stability per hand independently. For combined gestures, both per-hand monitors must independently reach stable state before the combined gesture can trigger. Never pass a concatenated multi-hand list to a single monitor.

**Warning signs:**
- Gestures never fire in 2-hand mode even when both hands are clearly motionless
- `stability_monitor.stable_frame_count` stays at 0 continuously
- Gestures work correctly with one hand, fail only when both hands are on screen simultaneously

**Phase to address:**
Same phase and same PR as CRITICAL-01 — both stem from the flat landmark list architecture and must be fixed together.

---

### CRITICAL-03: MediaPipe Handedness Labels Are Inverted on Pre-Flipped Frames

**What goes wrong:**
The frame flip (`cv2.flip(frame, 1)`) happens inside `CameraManager._loop_captura()` before the frame is stored in `_ultimo_frame`. By the time `HandTracker.processar()` receives the frame, it is already horizontally mirrored. MediaPipe processes this mirrored frame and assigns handedness labels from the perspective of the mirrored image. Result: `resultado.multi_handedness[i].classification[0].label == "Right"` identifies the hand appearing on the right side of the preview — which is the user's actual left hand. If the app exposes "Left hand gesture" / "Right hand gesture" labels in the UI or config based on MediaPipe's `multi_handedness`, they will be consistently swapped for all users using a front-facing webcam.

**Why it happens:**
MediaPipe handedness is assigned from the model's perspective of what it sees. The selfie convention is that a front-facing camera shows a mirror image, so "Right" in the mirrored image IS the user's left hand. Because the flip happens before MediaPipe sees the frame (inside `_loop_captura`), MediaPipe labels a non-selfie orientation but the user observes a selfie preview — the labels match the camera's raw orientation, not the user's physical body.

**How to avoid:**
Swap the handedness label after receiving it from MediaPipe: if MediaPipe says `"Right"`, treat it as `"Left"` in all app logic (and vice versa). This is a two-line fix in the code that reads `multi_handedness`. Alternatively, move the frame flip to after `HandTracker.processar()` — process the raw frame, then flip only the output frame for display — but this requires pipeline restructuring and should be evaluated separately.

**Warning signs:**
- Users report that "left hand gesture" fires when they raise their right hand
- Combined gesture configured as "left: OPEN_HAND + right: FIST" fires when hands are physically swapped
- The bug only manifests in a front-facing webcam setup; a rear-facing or document camera may show opposite or correct behavior

**Phase to address:**
2-hand detection phase, during the UI labeling and combined binding configuration task. Must be verified with a physical test: raise right hand, confirm UI labels it "Right."

---

### CRITICAL-04: pyvirtualcam Internal Loop Does Not Eliminate the MJPEG USB Lag

**What goes wrong:**
The proposed internal virtual camera loop (Thread A writes to pyvirtualcam, Thread B reads from it via `cv2.VideoCapture`) does not eliminate the root cause of the C920's 40-50ms lag. The lag originates in the USB MJPEG pipeline: the camera encodes frames as MJPEG on the sensor, transmits over USB, and the DirectShow driver decodes on the host CPU. `cv2.VideoCapture.read()` in Thread A still traverses this full pipeline before pyvirtualcam receives the decoded frame. Thread B then reads the same already-decoded frame from shared memory with additional memcopy overhead. Net result: the same 40-50ms hardware lag is present, plus the virtual cam roundtrip overhead. The user's observation that OBS Virtual Cam eliminates lag is because OBS configures the camera to deliver uncompressed YUY2 frames via MSMF — bypassing the MJPEG encode/decode cycle entirely — not because shared memory avoids lag.

**Why it happens:**
The assumption is "OBS Virtual Cam = no lag because shared memory." The actual causal mechanism is "OBS captures uncompressed frames, which have no encode/decode latency." Reproducing the fix requires changing the capture pixel format, not the delivery mechanism.

**How to avoid:**
Frame the internal virtual cam loop correctly: it reduces frame staleness and decouples the engine's read rate from the camera's hardware rate (genuine benefits from the existing `Condition`-based `ler_frame()`), but it does not reduce the fundamental capture latency on MJPEG cameras. The lag fix requires forcing uncompressed capture: use MSMF with `capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))`. Measure actual before/after latency numbers to validate any approach before shipping it as a "lag fix."

**Warning signs:**
- After enabling internal virtual cam loop, measured latency via `time.monotonic()` around `capture.read()` in Thread A is still 30-45ms
- The lag improvement appears only when FOURCC is changed to YUY2, not when the loop architecture changes
- User reports "still laggy" after the feature ships

**Phase to address:**
Low-latency capture phase. MSMF + FOURCC probe must be implemented and validated first. The virtual cam loop is a separate architectural feature with separate justification.

---

### CRITICAL-05: MSMF May Still Negotiate MJPEG Without Explicit FOURCC Override

**What goes wrong:**
`cv2.VideoCapture(index, cv2.CAP_MSMF)` opens the camera under Media Foundation but does not guarantee uncompressed capture. For C920-class cameras, MSMF negotiates the format that satisfies the requested FPS. At 60fps and 720p, the only available format is MJPEG — MSMF picks it silently. `isOpened()` returns `True`, frames arrive, but the MJPEG encode/decode cycle is still active. Latency is identical to `CAP_DSHOW`. There is no warning; `capture.get(cv2.CAP_PROP_FOURCC)` is the only way to detect this.

**Why it happens:**
OpenCV's MSMF backend delegates format negotiation to Windows Media Foundation, which optimizes for satisfying the requested FPS rather than choosing uncompressed formats. Developers assume "I switched to MSMF" implies a format change, without verifying what was actually negotiated.

**How to avoid:**
After opening with `CAP_MSMF`, explicitly set FOURCC before the first `read()`: `capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUY2'))`. Then verify: `actual_fourcc = capture.get(cv2.CAP_PROP_FOURCC)` — log the result. If the camera rejected YUY2 (still shows MJPG), lower the FPS target: C920 delivers YUY2 at up to 30fps at 720p but only MJPEG above 30fps. Accept the 30fps ceiling as the cost of uncompressed capture, or fall back gracefully to DSHOW with a user-visible note.

**Warning signs:**
- `capture.get(cv2.CAP_PROP_FOURCC)` returns `1196444237.0` (FOURCC for "MJPG") after opening with CAP_MSMF
- Latency measured via `time.monotonic()` around `capture.read()` is unchanged after switching to MSMF
- FPS drops to 30 when YUY2 is forced at 720p (expected — this is the camera hardware limit, not a bug)

**Phase to address:**
Low-latency capture phase. The MSMF probe must log negotiated FOURCC and actual FPS as part of the backend selection decision — not just `isOpened()`.

---

### CRITICAL-06: sleep_until_next_frame() Called From the Engine Thread Stalls the Gesture Loop

**What goes wrong:**
`CameraManager.enviar_para_virtual()` calls `self.virtual_camera.sleep_until_next_frame()`, which blocks the calling thread until the next frame slot according to the virtual cam's configured FPS. This method is currently invoked from `GestureEngine.run()` — the engine thread. In the internal virtual cam loop architecture, if the write path (`enviar_para_virtual`) remains in the engine thread, the engine thread simultaneously reads from the virtual cam AND sleeps for the write side's FPS timing. This creates an artificial FPS ceiling on gesture processing equal to the virtual cam's FPS setting. If the virtual cam is configured at 30fps, the engine is pinned to 30fps even if the physical camera delivers 60fps and `process_fps` is set higher.

**Why it happens:**
The current single-thread architecture has the engine both producing and consuming virtual cam frames. `sleep_until_next_frame()` was designed for a producer-side pacing call. When the architecture splits into Thread A (producer) and Thread B (consumer), `sleep_until_next_frame()` must move to Thread A, not remain in the engine thread (Thread B).

**How to avoid:**
The internal virtual cam loop requires Thread A to own its own write loop: `send()` + `sleep_until_next_frame()` at the virtual cam's FPS. The engine thread (Thread B) calls only `ler_frame()` and must never call `enviar_para_virtual()` in internal loop mode. Add an `_enable_internal_loop` flag to `CameraManager`; when set, `iniciar()` spawns Thread A and the `enviar_para_virtual()` method becomes a no-op for the engine path.

**Warning signs:**
- Engine FPS reported exactly equal to the virtual cam FPS config, even when camera delivers higher FPS
- Profiling shows the majority of engine loop time spent inside `enviar_para_virtual()` / `sleep_until_next_frame()`
- Removing the virtual cam write call from the engine loop immediately restores expected FPS

**Phase to address:**
Low-latency capture phase, as part of the internal loop architecture task.

---

## Moderate Pitfalls

---

### MODERATE-01: GestureEngine Single-Gesture State Machine Cannot Track Combined Hold Time Reliably

**What goes wrong:**
`GestureEngine.run()` tracks hold time via `gesto_ativo`, `inicio_gesto`, and `ultimo_disparo_por_gesto` — all keyed to a single string. For combined gestures, both hands must hold their respective gestures simultaneously for the full `hold_time`. The current state machine resets `inicio_gesto = None` any time `gesto` is falsy (either hand drops out). In 2-hand mode with MediaPipe's normal tracking, one hand will occasionally produce `None` for a single frame due to a lighting glitch or partial occlusion. Each such miss resets the combined gesture timer to zero. The UX result: combined gestures feel impossible to trigger because any one-frame tracking gap requires restarting the full hold timer.

**Why it happens:**
The "reset on gesture absence" logic was appropriate and correct for single-hand detection, where a `None` frame genuinely means the hand left the frame. For combined gestures, a transient miss in one hand is a tracking artifact, not user intent.

**How to avoid:**
Implement a small tolerance window for combined gesture state: allow up to N consecutive frames of "partial detection" (only one of the two expected hands detected) before resetting the combined timer. Track `combo_gesto_ativo`, `combo_inicio_gesto`, `combo_ultimo_disparo` separately from single-hand state — do not share state between the two detection paths. N=2 (skip 2 consecutive partial frames) is a reasonable starting value given the 7-frame detection window already in place.

**Warning signs:**
- Combined gestures only fire when both hands are held perfectly motionless with no tracking gaps whatsoever
- Single-hand gestures fire reliably at 0.5s hold time, but equivalent combined gestures require 5x that time
- Logs show `gesto_ativo = None` and then the gesture label alternating multiple times per second

**Phase to address:**
2-hand detection phase, engine state machine task — after CRITICAL-01 and CRITICAL-02 are resolved.

---

### MODERATE-02: MSMF isOpened() Returns True When No Frames Are Delivered

**What goes wrong:**
`cv2.VideoCapture(index, cv2.CAP_MSMF).isOpened()` returns `True` on some cameras or Windows configurations even when the device fails to initialize properly under Media Foundation. The first several `read()` calls return `(False, None)`. The existing `GestureEngine.run()` checks `if not self.camera.capture.isOpened()` immediately after `camera.iniciar()` and emits "Falha ao iniciar câmera" if False — but `isOpened()` says True. The engine proceeds into the main loop and silently spins on failed reads. The user sees no error message but the preview is black and no gestures fire.

**Why it happens:**
OpenCV's `isOpened()` verifies that the `VideoCapture` object was successfully constructed, not that the underlying device delivered a valid frame. MSMF initialization involves asynchronous driver negotiation — the device may not be ready for the first few frames after `open()` returns.

**How to avoid:**
After opening with MSMF, perform a warm-up probe: attempt 5 `read()` calls in the capture thread and verify at least one returns a valid non-None frame before declaring the camera ready. Gate the engine's main loop on a `camera_ready` event that `CameraManager.iniciar()` sets only after a successful warm-up frame, not immediately after `VideoCapture()` construction.

**Warning signs:**
- `isOpened()` returns `True` but the first N `read()` calls return `(False, None)` in the capture thread
- Engine starts, `status_changed` emits "Câmera iniciada", but preview remains black
- Only reproducible with `CAP_MSMF`; the same camera opens reliably with `CAP_DSHOW`

**Phase to address:**
Low-latency capture phase, in the MSMF probe implementation.

---

### MODERATE-03: Config Schema for Combined Bindings Must Be Chosen Before Any Engine Code Depends on It

**What goes wrong:**
The combined gesture bindings key needs a schema that maps a two-hand gesture pair to an action config. If designed as `{"Mão aberta+Punho": {...}}` using display names (matching the existing single-hand convention), the engine must split the compound key on `"+"`, then run each half through `GESTURE_ALIASES` normalization — error-prone and fragile to gesture name changes. If designed correctly as `{"OPEN_HAND+FIST": {...}}` using canonical codes, no alias resolution is needed on the key. Choosing the wrong schema up front, then having user configs saved with it, requires a migration script in the next patch.

**Why it happens:**
The single-hand binding schema in `config.json` uses Portuguese display names as keys ("Joinha", "Mão aberta"). `GESTURE_ALIASES` normalizes these at engine load time. Extending the same pattern to compound keys requires splitting and normalizing both halves — an error-prone operation that compounds the existing alias complexity.

**How to avoid:**
Use canonical internal codes (the same codes `GestureDetector.detectar()` emits) as keys in `combined_bindings`, not display names. Schema: `"combined_bindings": {"OPEN_HAND+FIST": { ...same action fields as single bindings... }}`. The UI displays friendly names but stores canonical codes. Also add `"config_version": 2` to `config.json` now — before v1.2 ships — so any future migration has a clean baseline to branch on.

**Warning signs:**
- Engine code needs to import `GESTURE_ALIASES` to parse combined binding keys
- A combined gesture configured in the UI fires for the physically opposite hand combination
- A config written by v1.2 triggers a `KeyError` in the engine when an old GESTURE_ALIAS entry is renamed

**Phase to address:**
Config schema task at the start of the 2-hand detection phase, before any engine logic is written that reads `combined_bindings`.

---

### MODERATE-04: Virtual Camera Device Index Is Not Predictable Across Machines

**What goes wrong:**
When Thread A creates a `pyvirtualcam.Camera(...)` and Thread B reads from it via `cv2.VideoCapture(virtual_cam_index, ...)`, the integer index of the virtual camera device is not constant. It depends on how many physical cameras and other virtual cameras (e.g., OBS Virtual Camera) are installed. On a clean system the virtual cam might be index 1, but on a streamer's machine with OBS already active, it might be index 2 or 3. Hardcoding index 1 fails on single-camera systems and on machines where another virtual cam occupies index 1 first.

**Why it happens:**
`cv2.VideoCapture` enumerates devices by integer index with no direct way to open by device name. There is no stable mapping between device name and index across different machine configurations.

**How to avoid:**
After `pyvirtualcam.Camera(...)` is created, read `pyvirtualcam.Camera.device` to get the device name string. Enumerate video inputs via `pygrabber.ds.VideoInput.get_video_devices()` (already an optional dependency in the project) or `QMediaDevices.videoInputs()` and match the device name to find the correct `cv2.VideoCapture` index. Fall back to probing indices 0-5: open each, read one frame, check if dimensions match the expected virtual cam dimensions, and accept the first match.

**Warning signs:**
- Internal loop works on the developer's machine but Thread B opens the wrong camera on other machines
- `cv2.VideoCapture(1).read()` returns the physical webcam's frame instead of the virtual cam's frame
- The bug is intermittent — appears only when OBS is also running

**Phase to address:**
Low-latency capture phase, as part of the internal loop implementation.

---

### MODERATE-05: Existing Config Files Miss New Fields — Must Default Silently

**What goes wrong:**
All existing `config.json` files lack `max_maos`, `combined_bindings`, the MSMF backend toggle, and the virtual cam mode flag. If any of these new fields are accessed without a `.get(key, default)` fallback, the engine raises a `KeyError` at startup for any user with an existing config. The current `_setup()` in `GestureEngine` is careful with `.get()` defaults for all fields — but new v1.2 code may not follow the same discipline, especially in rushed implementation.

**Why it happens:**
New features add new config keys. Without a config migration step or strict defaulting, the new code touches keys that don't exist in existing files.

**How to avoid:**
Every new config key access must use `.get(key, default)` with an explicit, correct default — never bare dict subscript `config["new_key"]`. The defaults must be safe values that produce the existing v1.1 behavior (e.g., `max_maos=1` means single-hand mode, `msmf_enabled=False` means stay on DSHOW, `combined_bindings={}` means no combined gestures). Add a startup migration check: if `config_version` is absent or below 2, write the missing keys with their defaults atomically before proceeding.

**Warning signs:**
- `KeyError` at engine startup when user has an existing config
- The app starts correctly on a fresh install (new config) but crashes on upgrade (existing config)
- New features are "off" by default on fresh install but crash on existing installs

**Phase to address:**
Config schema task at the start of the 2-hand detection phase (same task as MODERATE-03).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep flat landmark list; handle 42-point case in detectar() with an if/else | No HandTracker API refactoring | detectar() becomes a maze; GestureStabilityMonitor still breaks; combined detection requires index-splitting anyway | Never — per-hand list is the correct data structure |
| Skip FOURCC verification after MSMF open | Less code | MSMF silently stays on MJPEG; lag "fix" does not work; impossible to debug why C920 still lags | Never — verification is two lines |
| Use display names as combined binding keys (matching single-hand convention) | UI-to-config name consistency | Alias normalization on compound string keys; migration pain when gesture names change | Never — canonical codes are cheaper |
| Omit config_version field from v1.2 schema | One fewer field | Future migrations have no clean baseline to branch on | Acceptable only if all new keys are backward-compatible with absent defaults |
| Call sleep_until_next_frame() from engine thread in internal loop mode | Reuse existing enviar_para_virtual() unchanged | Engine FPS capped to virtual cam FPS, defeating the performance purpose | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| MediaPipe + pre-flipped frame | Reading multi_handedness labels directly | Swap "Left"/"Right" after reading from MediaPipe, because the frame is already flipped when MediaPipe sees it |
| pyvirtualcam write + cv2.VideoCapture read | Assuming cv2 delivers BGR from virtual cam | Verify channel order with a known-color test frame — virtual cam driver may deliver RGB or BGR depending on the backend |
| MSMF + C920 at 60fps | Expecting MSMF to auto-pick YUY2 | C920 only delivers YUY2 up to 30fps at 720p; explicitly set FOURCC=YUY2 and accept the 30fps ceiling |
| GestureStabilityMonitor + 2 hands | Reusing one monitor for a 42-point flat list | One monitor per hand; coordinate stable states at the combined gesture layer |
| MSMF probe + isOpened() | Declaring success on isOpened() == True | Perform 5 warm-up reads; only set camera_ready after at least one valid frame is received |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| max_num_hands=2 without profiling FPS impact | FPS drops from 28-35 to 15-20; hold times become unreliable | Benchmark first; keep model_complexity=0 mandatory for 2-hand mode | When both hands are fully visible simultaneously |
| sleep_until_next_frame() in engine thread | Engine FPS pinned exactly to virtual cam FPS regardless of camera speed | Move sleep call to dedicated write thread (Thread A) | Always — any time engine thread calls enviar_para_virtual() in internal loop mode |
| Combined gesture detection window shared with single-hand window | Stale single-hand entries pollute combined gesture voting | Keep combined gesture state machine fully separate from single-hand state | When user rapidly alternates between one-hand and two-hand gestures |
| MSMF + YUY2 at 60fps attempt | Camera silently downclocks to 30fps | Check capture.get(cv2.CAP_PROP_FPS) after setting FOURCC; log actual negotiated FPS | For 720p capture on C920-class cameras |

---

## "Looks Done But Isn't" Checklist

- [ ] **MSMF support:** "Opened successfully" — verify `capture.get(cv2.CAP_PROP_FOURCC)` shows YUY2 (not MJPG) AND latency measured via `time.monotonic()` around `capture.read()` is measurably lower than the DirectShow baseline
- [ ] **2-hand detection enabled:** "Both skeletons draw on screen" — verify single-hand gestures still fire when only one hand is visible; verify combined gestures fire at the configured hold_time with tolerance for 1-2 missed tracking frames
- [ ] **Handedness labels:** "Left/Right labels appear in UI" — physical test: raise right hand only, confirm UI and config label it "Right" (not "Left")
- [ ] **Internal virtual cam loop:** "Engine reads from virtual cam" — verify Thread A and Thread B are separate threads; engine thread does NOT call `sleep_until_next_frame()`
- [ ] **Config migration:** "App starts with old config.json" — load a v1.1 config (missing `max_maos`, `combined_bindings`) and verify the app starts silently in 1-hand mode with no `KeyError` or exception
- [ ] **pyvirtualcam missing driver:** "Virtual cam enabled in config" — simulate no virtual cam driver; verify graceful error message and fallback to direct capture mode
- [ ] **Combined gesture cooldown:** "Combined gesture fired" — verify `ultimo_disparo_por_gesto` uses the full compound key (e.g., `"OPEN_HAND+FIST"`) not either individual hand key, so combined and single-hand cooldowns do not interfere

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Flat landmark list shipped; 2-hand users report all gestures broken | HIGH | Hotfix: refactor HandTracker.processar() to return List[List]; update GestureEngine and GestureStabilityMonitor in same PR; release patch immediately |
| Wrong handedness labels in saved user configs | MEDIUM | Write config migration on load: iterate combined_bindings and swap "left"/"right" key values; write corrected config atomically; add config_version bump |
| MSMF shipped without FOURCC probe; lag not eliminated | LOW | Patch: add FOURCC=YUY2 after MSMF open; log negotiated format; expose as advanced config option |
| sleep_until_next_frame() left in engine thread; FPS capped | MEDIUM | Refactor: spawn dedicated write thread in CameraManager; move sleep call to write thread loop; engine thread reads only |
| Combined bindings schema wrong; user configs are invalid | HIGH | Add schema migration function: read v1 compound key format, transform to v2 format, write atomically on first v1.2 launch |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Flat landmark list breaks detectar() with 2 hands | First task of 2-hand detection phase | Show 2 hands: single-hand gestures still fire; show 1 hand: gestures fire normally |
| GestureStabilityMonitor breaks on hand count change | First task of 2-hand detection phase (same PR) | Wave one hand while holding gesture with the other: gesture still fires |
| Handedness labels inverted on flipped frames | 2-hand detection phase, UI labeling task | Physical test: right hand up = "Right" label in UI |
| pyvirtualcam loop does not eliminate MJPEG lag | Low-latency capture phase — measure before and after | time.monotonic() around capture.read(): target <10ms vs current 40-50ms baseline |
| MSMF still negotiates MJPEG without FOURCC | Low-latency capture phase, MSMF probe | capture.get(cv2.CAP_PROP_FOURCC) logged after open; must show YUY2 on C920 |
| sleep_until_next_frame() stalls engine thread | Low-latency capture phase, internal loop architecture | Profile: engine FPS must match process_fps config, not virtual cam FPS |
| Combined gesture hold time unreliable | 2-hand detection phase, engine state machine | Configure 1s hold time: combined gesture fires within 1.5s under normal use with occasional tracking gaps |
| MSMF isOpened() gives false positive | Low-latency capture phase, MSMF probe | Probe MSMF with unsupported camera: "Falha ao iniciar câmera" emitted, not silent black preview |
| Combined binding schema drift | First task of 2-hand detection phase | Load v1.1 config.json (no combined_bindings key): app starts in 1-hand mode with no exception |
| Virtual cam device index unpredictable | Low-latency capture phase, internal loop | Test with OBS also running: correct virtual cam device opened, not OBS's device |

---

## Sources

- Direct inspection of `core/camera.py` (CameraManager, `_loop_captura`, `ler_frame`, `enviar_para_virtual`), `core/hand_tracker.py` (flat landmark list in `processar()`), `core/gesture_detector.py` (`len(pontos) != 21` guard in `detectar()`), `engine/gesture_engine.py` (GestureStabilityMonitor, single-gesture state machine), `config.json` (existing schema, no combined_bindings or max_maos) — all v1.1 codebase as of 2026-06-26
- `.planning/todos/pending/2026-06-26-low-latency-capture-via-backend-alternativo-e-camera-virtual.md`
- `.planning/todos/pending/2026-06-26-deteccao-de-2-maos-e-gestos-combinados.md`
- MediaPipe Hands API: handedness is labeled from the perspective of the observed hand image; on a mirrored (selfie) frame, "Right" in the image = user's left hand
- OpenCV MSMF backend: FOURCC negotiation behavior and isOpened() false positive on Windows are documented community issues (GitHub opencv/opencv issues area, multiple reports)
- pyvirtualcam documentation: sleep_until_next_frame() is a producer-side pacing call; calling it from the consumer thread introduces unintended FPS coupling

---
*Pitfalls research for: OBS GestureNode v1.2 — MSMF backend, internal virtual camera loop, 2-hand MediaPipe detection*
*Researched: 2026-06-26*
