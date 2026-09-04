# Project Research Summary

**Project:** OBS GestureNode v1.2
**Domain:** Desktop gesture-control app for streamers (Windows, Python/PySide6 + OpenCV + MediaPipe)
**Researched:** 2026-06-26
**Confidence:** MEDIUM-HIGH (codebase inspected directly; external claims cross-checked via multiple sources)

---

## Executive Summary

OBS GestureNode v1.2 is a stabilization-and-extension milestone on top of a well-structured v1.1 foundation. The core architecture — a condition-based camera capture thread feeding a `GestureEngine` QThread that calls MediaPipe and dispatches actions via a `ThreadPoolExecutor` — is solid and does not need replacement. The two major additions for v1.2 are: (1) a latency measurement and disclosure system for camera capture, and (2) 2-hand gesture detection with configurable combined gesture bindings. Both additions have clear integration points and localized file changes; neither requires architectural surgery.

The single most important finding that redefines the v1.2 scope: **neither CAP_MSMF as a backend switch nor an internal pyvirtualcam relay loop are viable lag-reduction strategies**. CAP_MSMF imposes 80+ second initialization on MJPEG cameras like the C920 and does not bypass the MJPEG encode/decode latency floor. The virtual cam relay loop is blocked by OpenCV returning blank frames from the OBS Virtual Camera device and adds no latency benefit even if it worked. The correct strategy for v1.2's camera work is to measure latency on the first N frames and display a passive badge to the user — and if lag exceeds a threshold, provide guided instructions for using the OBS Virtual Camera (which bypasses the MJPEG pipeline via hardware-accelerated decode inside OBS itself).

The 2-hand detection feature has one critical prerequisite that governs phase ordering: `HandTracker.processar()` currently returns a flat 21-point list that silently breaks when `max_num_hands=2` is set (a 42-point list causes `GestureDetector.detectar()` to unconditionally return `None`). The `HandTracker` API must be changed to return a `list[dict]` with per-hand landmarks and handedness label before any other 2-hand work can proceed. This change must be committed atomically with `GestureEngine` updates — the two files cannot be changed independently. `GestureDetector.detectar()` itself remains unchanged; combined gesture logic lives in the engine layer. The UX anchor for combined gestures is 6 pre-defined streamer combos (Go Live, Encerrar, BRB, Celebrar, Gravar, Câmera Off) that populate as selectable presets in the UI.

---

## Key Findings

### Recommended Stack

The v1.1 stack carries forward unchanged. `mediapipe==0.10.14` remains pinned — the new Tasks API requires a complete HandTracker rewrite and is out of scope. For 2-hand mode, `max_num_hands=2` is the only constructor change needed; `model_complexity=0` (lite) is mandatory to stay within the 20–28 FPS window on CPU-only hardware. No new Python dependencies are required for v1.2 features.

**Core technologies (unchanged):**
- `mediapipe==0.10.14` (pinned) — do not upgrade; Tasks API migration is a v2.0 item
- `opencv-python` with `cv2.CAP_DSHOW` — stay on DirectShow; MSMF initialization time disqualifies it
- `PySide6` — `QThread`, `QButtonGroup`, signals/slots for engine restart on mode change
- `pyvirtualcam` — OUTPUT only; the internal relay loop is not viable on Windows
- `obsws-python` — unchanged; relevant for guided OBS VCam instruction flow

**Non-changes explicitly confirmed by research:**
- No CAP_MSMF integration
- No internal pyvirtualcam relay thread
- No Unity Capture installation requirement
- No mediapipe upgrade

### Expected Features

**Must have (table stakes):**
- Camera opens within 2–3 seconds (DirectShow baseline already met)
- Both hand skeletons visible on preview when 2-hand mode is active
- Combined gesture fires only when BOTH hands match for the full hold_time
- Single-hand gestures continue to work correctly in 2-hand mode (backward compatibility)
- Existing `config.json` files load without error under v1.2 (silent defaults for all new keys)

**Should have (differentiators):**
- Passive latency badge in Geral tab ("● 45ms — OK") — green/amber/red, no modal
- 6 pre-defined combined gesture presets (Go Live, Encerrar, BRB, Celebrar, Gravar, Câmera Off)
- Live per-hand gesture preview during combo configuration ("Esquerda: Punho | Direita: Paz")
- Dual hold-time progress bars on preview frame for 2-hand mode
- Position-based handedness fallback when MediaPipe confidence < 0.75

**Defer to v2+:**
- CAP_MSMF backend (80+ second initialization — not viable for MJPEG cameras)
- Internal virtual cam relay loop (DirectShow blank-frame bug + no latency benefit)
- Temporal sequence gestures — state machine complexity
- Per-hand independent hold_time — confusing UX

### Architecture Approach

All v1.2 changes are additive extensions to existing modules. No new files required for core features. The pipeline shape — `CameraManager` → `GestureEngine (QThread)` → `GestureDetector` → `ActionManager` — is unchanged.

**Modified components:**

| File | Change Type | Summary |
|------|-------------|---------|
| `core/hand_tracker.py` | API change | `processar()` returns `(frame, list[dict])` — each dict: `{"handedness": "Left"\|"Right", "landmarks": list[tuple]}`. Constructor gains `max_num_maos: int = 1`. |
| `engine/gesture_engine.py` | 2-hand pipeline | Iterates `maos_detectadas`; per-hand `GestureStabilityMonitor` pair; `combined_bindings` property; `_normalize_gesture_keys()` handles `+` compound keys. |
| `core/gesture_detector.py` | New method only | `detectar_par(pontos_esq, pontos_dir)` → `"GESTO_ESQ+GESTO_DIR"` or None. `detectar()` unchanged. |
| `core/camera.py` | Latency measurement | First-N-frames timing in `_loop_captura`; exposes `_lag_medido_ms`. No relay thread, no MSMF. |
| `ui/tabs/geral_tab.py` | New widgets | Hand count toggle (1/2 mãos radio group) + latency badge |
| `ui/tabs/gestos_tab.py` | New section | Combined gesture section with `CombinedGestureDialog`, 6 preset combos |
| `ui/main_window.py` | Wiring | Wires hand mode toggle to `restart_engine()`; loads/saves `combined_bindings` |
| `config.json` | Schema v2 | New fields: `gestures.max_maos`, `gestures.combined_bindings`, `config_version: 2` |

### Critical Pitfalls

1. **Flat landmark list breaks silently with 2 hands** — `GestureDetector.detectar()` has `if len(pontos) != 21: return None`. With `max_num_hands=2`, the flat merged list has 42 points; all gesture detection silently returns None. Fix first, before any other 2-hand work. Atomic commit: `hand_tracker.py` + `gesture_engine.py` together.

2. **`GestureStabilityMonitor` collapses on hand-count change** — the monitor returns `float('inf')` movement when landmark count changes frame-to-frame. In 2-hand mode, one hand entering/leaving frame is the common case, permanently blocking gesture dispatch. One monitor instance per hand; never pass a merged list.

3. **Handedness labels inverted on pre-flipped frames** — `CameraManager._loop_captura()` already applies `cv2.flip(frame, 1)` before storing frames. MediaPipe's `"Right"` = the user's physical left hand. Swap Left/Right after reading `multi_handedness` — two-line fix in `hand_tracker.py`. Verify with physical test: raise right hand, confirm "Right" label.

4. **CAP_MSMF and virtual cam relay are non-viable** — MSMF causes 80+ second camera open on MJPEG hardware. Virtual cam relay hits OpenCV blank-frame bug (issue #19746). The lag floor (42–52ms for C920 MJPEG) is hardware-intrinsic; measure and disclose, do not attempt to fix with a backend switch.

5. **Config migration required for existing users** — new fields absent in v1.1 `config.json`. Every new field must use `.get(key, default)`. Add `config_version: 2` and a startup migration check.

---

## Implications for Roadmap

Suggested 6-phase structure (continuing phase numbering from v1.1 Phase 7):

### Phase 8: HandTracker API Refactor
Hard prerequisite for all 2-hand work. Fixes CRITICAL-01/02/03 atomically.
- `processar()` returns `list[dict]` with per-hand landmarks + handedness label
- Constructor gains `max_num_maos: int = 1`
- `GestureEngine.run()` updated atomically in same commit
- Handedness swap applied (MediaPipe "Right" → user's physical right)
- **Smoke test:** raise right hand → confirm "Right" label; run 1-hand smoke test to confirm no regression

### Phase 9: Config Schema + Combined Gesture Detection Engine
Locks schema before any UI saves combined bindings.
- `config.json` v2 schema: `max_maos`, `combined_bindings`, `config_version: 2`
- Startup migration guard (`.get(key, default)` for all new fields)
- `GestureDetector.detectar_par()` new method
- `GestureEngine` 2-hand pipeline: per-hand detection + `"{left}+{right}"` combined key lookup
- **Smoke test:** load a v1.1 `config.json` → app starts in 1-hand mode silently, no exception

### Phase 10: Combined Gesture UI + 6 Pre-defined Presets
Wires UI onto Phases 8–9. Hand count toggle triggers `restart_engine()`.
- Radio group "1 mão / 2 mãos" in GeralTab
- `CombinedGestureDialog` in GestosTab with left/right gesture dropdowns
- 6 streamer combo presets: Go Live (🖐+🖐), Encerrar (✊+✊), BRB (✊+🖐), Celebrar (👍+👍), Gravar (✊+👍), Câmera Off (🤙+🤙)
- `main_window.py` wiring for combined_bindings load/save
- **Smoke test:** configure a preset combo; verify saved key is canonical code (`"OPEN_PALM+OPEN_PALM"`, not display name)

### Phase 11: Preview Overlay (UX-05, UX-06)
Completion signal for the gesture feature. 2-hand variant needs Phase 8 per-hand data.
- Gesture name overlay on preview frame
- Hold-time progress bar (single and dual for 2-hand mode)
- Flash visual on action fire
- Per-hand labels spatially positioned ("Esquerda: Punho" left, "Direita: Paz" right)

### Phase 12: Camera Latency Measurement + Passive Badge (CAM-07, CAM-06 redefined)
Independent of 2-hand track. Placed after to avoid concurrent `camera.py` changes.
- First-N-frames latency measurement in `_loop_captura`
- Passive green/amber/red badge in GeralTab (no modal)
- If lag > 80ms threshold: display guided OBS VCam instruction text
- **Explicitly excludes:** CAP_MSMF, virtual cam relay loop
- **Smoke test:** verify no `capture.get(cv2.CAP_PROP_FOURCC)` call introduced

### Phase 13: Onboarding, Visual Redesign + Platform Abstraction (UX-07–09, UI-01–04, PLT-01–03)
Last phase — highest file-change surface, highest merge-conflict risk.
- First-run onboarding checklist (UX-09)
- Inline field validation (UX-07, UX-08)
- Dark mode default, consistent palette, hover states, componentized gesture cards (UI-01–04)
- Platform abstraction: `platform/_windows.py`, `platform/_protocol.py`, ActionManager dependency injection (PLT-01–03)

### Phase Ordering Rationale

- Phase 8 must be first — CRITICAL-01/02/03 block the entire 2-hand track
- Phase 9 before Phase 10 — schema must exist before UI can save combined bindings
- Phase 12 is independent of the 2-hand track — can be planned in parallel with Phase 9/10 but executed sequentially to avoid concurrent `camera.py` changes
- Phase 13 is always last — platform abstraction has the highest merge-conflict risk

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Codebase inspected directly; MSMF/virtual cam findings cross-checked via OpenCV issues #17687, #19746, #27917 |
| Features | MEDIUM | Table stakes from codebase inspection (HIGH); UX patterns from VTubeStudio ecosystem (LOW) |
| Architecture | HIGH | All integration points from direct source inspection |
| Pitfalls | HIGH | CRITICAL-01/02/03 from direct code inspection of `detectar()` guard, `processar()` return, `_loop_captura` flip timing |

### Gaps to Address in Planning

- **Handedness swap exact location:** Confirm in Phase 8 physical smoke test
- **2-hand FPS floor on target hardware:** Estimated 20–28 FPS; document ceiling in Geral tab if below 20
- **Guided OBS VCam instruction form (Phase 12):** Define precisely during Phase 12 planning — static text, link, or obsws-python check

---

## Sources

### Primary (HIGH — direct codebase inspection)
- `core/camera.py`, `core/hand_tracker.py`, `core/gesture_detector.py`, `engine/gesture_engine.py`, `config.json`

### Secondary (MEDIUM — official documentation)
- MediaPipe 0.10.14 `mp.solutions.hands` API; handedness mirror convention
- pyvirtualcam Windows backends — letmaik.github.io/pyvirtualcam

### Tertiary (LOW — community reports, cross-checked)
- OpenCV issues #17687, #27917: CAP_MSMF 80+ second init on MJPEG cameras
- OpenCV issue #19746, OBS issue #3635: `cv2.VideoCapture` returns blank frames from OBS Virtual Camera
- MediaPipe issue #3047: handedness unreliable at frame edges
- VTubeStudio wiki: 2-hand gesture binding UX reference

---
*Research completed: 2026-06-26 | Ready for roadmap: yes*
