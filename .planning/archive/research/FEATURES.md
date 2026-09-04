# Feature Landscape — OBS GestureNode v1.2

**Domain:** Desktop gesture-control app for streamers (Windows, Python/PySide6)
**Scope:** v1.2 "Features & Polish" — low-latency camera capture + 2-hand gesture detection (new) + UX/UI polish (carry-over from v1.1)
**Researched:** 2026-06-26
**Overall confidence:** MEDIUM (technical constraints confirmed via OpenCV/MediaPipe/pyvirtualcam docs; UX patterns cross-referenced against VTubeStudio and gesture app ecosystem; handedness reliability documented via GitHub issue tracker)

---

## Critical Research Findings (Read First)

These findings overturn assumptions in the TODO files and must shape requirement decisions:

### Finding 1 — MSMF will NOT reduce MJPEG lag (CAM-05 premise is wrong)

`cv2.CAP_MSMF` on Windows has WORSE initial frame acquisition than `cv2.CAP_DSHOW` for MJPEG cameras. It can take minutes to open the camera when resolution parameters are set. MSMF also cannot set MJPEG format programmatically. The root cause of lag on cameras like the Logitech C920 is the MJPEG encode/decode pipeline over USB — neither backend eliminates this at the driver level.

**Implication:** CAM-05 (try MSMF first) should be removed or rephrased. Testing MSMF will waste user startup time. The correct mitigation path is the threaded capture approach already partially implemented.

### Finding 2 — pyvirtualcam internal loop requires a pre-installed driver (CAM-06 constraint)

`pyvirtualcam` on Windows requires either the **OBS Virtual Camera** (bundled with OBS since v26) or **Unity Capture** driver to be installed. Since the app's users are OBS users, OBS is present — but OBS's virtual camera is a single-instance device: pyvirtualcam cannot write frames to it while OBS itself also uses it (e.g., as a source for streaming). The Unity Capture driver avoids this conflict but requires separate installation — violating the "no external software" constraint.

**Implication:** The "Thread A writes to virtual cam → Thread B reads from virtual cam" loop is not zero-config. The actual solution is a shared in-process frame buffer (already the architecture of `core/camera.py`'s condition-based `ler_frame`). The virtual cam path is a fallback-of-last-resort, not the primary strategy.

### Finding 3 — MediaPipe handedness requires a horizontally-flipped input frame

MediaPipe Hands assumes the input is a **mirrored (selfie/front-facing) frame**. OpenCV `VideoCapture` does NOT flip by default. If the frame passed to MediaPipe is not flipped with `cv2.flip(frame, 1)`, the Left/Right labels are swapped. The existing codebase applies `cv2.flip(frame, 1)` for the preview display but the detection input path must be audited.

Additionally, handedness classification becomes unreliable when a hand is near the frame edge or when both hands partially overlap. The error rate in edge cases is documented but not quantified officially.

**Implication:** Left/right semantic binding is feasible but requires (a) confirmed flipped input to MediaPipe, and (b) a stability buffer on handedness to avoid frame-to-frame flipping. Position-based inference (which half of the frame the hand centroid is in) is a more reliable fallback.

---

## Section 1 — Low-Latency Camera Capture

### Table Stakes

Features that users expect silently. If broken, the app feels unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Camera opens within 2–3 seconds | Every video app has this baseline | Low | DirectShow is fast; MSMF is not — avoid MSMF |
| Lag under 100ms from gesture to action | Streamers need real-time response | Medium | Already partially achieved via threaded capture + CAP_PROP_BUFFERSIZE=1 (git log shows 42–52ms) |
| No configuration required to reduce lag | Core promise: zero-setup for streamers | Medium | Real solution: single-slot buffer in capture thread (drop stale frames) |
| Camera status visible during startup | User needs to know the camera is initializing | Low | Status label in Geral tab already exists |
| No camera stuck / "camera occupied" on exit | Must release camera cleanly | Low | Already fixed in v1.1 |

### Differentiators

Features that go beyond baseline and build trust.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Latency measurement + passive status badge | Shows user the app is self-aware ("Camera: 45ms") | Medium | First N frames measured; no modal |
| Automatic fallback strategy with silent retry | Tests capture quality, applies fix transparently | Medium | NOT via MSMF; via buffer tuning |
| Tooltip disclosure of what was optimized | Power users can see why the app changed behavior | Low | Tooltip on the latency badge, not a dialog |
| Camera backend label in log/status (not a setting) | Informative without being technical | Low | Log line "Câmera iniciada: DirectShow, 720p, ~45ms" |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| User-facing backend selector (MSMF vs DirectShow) | Wrong solution; MSMF makes things worse for MJPEG | Measure lag, apply transparent fix |
| "Activate camera virtual mode" toggle | Requires OBS VirtualCam single-instance; not zero-config | Use in-process frame buffer (already in core/camera.py) |
| Modal dialog when high latency detected | Interrupts stream setup; streamers can't afford pop-ups | Passive amber badge in status area |
| Forced MSMF test on every startup | Adds seconds of startup delay for no benefit | Skip MSMF entirely |
| Prompting user to install Unity Capture | Violates no-external-software constraint | Use shared memory buffer inside the process |

### UX Behavior: Backend Auto-Selection

**Recommended pattern:** The app makes no changes to backend (stays with DirectShow). It measures round-trip latency on the first 10 frames. If lag > 60ms, it applies buffer-depth reduction aggressively (already done). It shows a passive inline badge in the camera section of the Geral tab — one line, no interaction required:

```
Camera: Logitech C920  [● 45ms — OK]
```

Badge is green (< 40ms), amber (40–80ms), red (> 80ms). Hovering the badge shows a one-line tooltip: "Latência medida nos primeiros 10 frames". No modal. No setting. The user does not need to act.

If the app later adds the internal buffer path as a workaround, it logs a single line to the in-app log: "Modo buffer ativado — lag reduzido de 65ms para 38ms" without any dialog.

### Complexity Estimate

| Sub-feature | Estimate | Risk |
|-------------|----------|------|
| Remove MSMF test path (CAM-05 revision) | Trivial (do not implement) | None |
| Latency measurement on first N frames | Low (timing already in codebase) | Low |
| Passive latency badge in Geral tab | Low (QLabel + color + tooltip) | Low |
| Internal buffer-depth tuning (already in CAP_PROP_BUFFERSIZE=1) | Already done | None |
| Virtual cam internal loop (CAM-06) | High + blocker (driver constraint) | HIGH — defer to v2 |

**Verdict on CAM-06:** The virtual cam internal loop is not implementable under the "no external software" constraint without Unity Capture. If the C920 lag persists after buffer tuning, the correct resolution is platform documentation ("C920 has hardware MJPEG lag; use your laptop's integrated webcam for gesture detection"). Defer CAM-06 to v2.0.

---

## Section 2 — 2-Hand Gesture Detection

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Mode toggle (1-hand vs 2-hand) in settings | Users must opt in — 2-hand has tradeoffs (stability, performance) | Low | Radio/toggle in Geral tab; persisted as `max_maos` in config |
| Both hands tracked in preview when 2-hand mode active | Visual confirmation that detection is working | Low | MediaPipe max_num_hands=2 returns list; overlay both skeletons |
| L+R gesture combo → action binding | Core feature of 2-hand mode | Medium | New section in Gestos tab; 2 dropdowns + action picker |
| Combined gesture fires only when BOTH hands match | Correct and expected behavior | Low | AND logic is the only logic needed for v1.2; OR adds noise |
| Cooldown and hold_time as single unit for combined gesture | Prevents double-triggering | Medium | GestureStabilityMonitor must aggregate, not gate per hand |
| Gesture overlay shows both hands independently | Preview feedback for setup and live use | Low | Draw per-hand labels on frame |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Pre-defined useful combined gestures | Onboarding shortcut for streamers; reduces blank-slate paralysis | Low | 4–6 preset combos in the UI |
| Live preview of both detected gestures while configuring a binding | User sees "Left: Fist, Right: Paz" while picking the combo | Medium | Same frame overlay pattern as existing gesture name display |
| Per-hand gesture label in preview (spatial, not just text) | Shows which label is left vs right in the camera view | Low | "Esquerda: Fist" left-anchored, "Direita: Paz" right-anchored on frame |
| Position-based handedness fallback | More reliable than MediaPipe's label when hands near edge | Medium | If centroid X < frame_width/2 → left side; else → right side |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Strict left/right semantic binding via MediaPipe label only | Unreliable at edges and when hands overlap | Add position-based fallback; accept heuristic match |
| AND/OR logic toggle for hand activation | Adds UI complexity; OR creates too many false positives | AND only for v1.2 |
| Overlap/touching hand gestures (e.g., clap, prayer) | MediaPipe landmark quality degrades when hands occlude | Only configure non-overlapping gestures |
| Temporal sequence gestures (gesture A then gesture B) | Much more complex state machine | Roadmap for v2.0 |
| Per-hand hold_time (left=0.8s, right=1.2s) | Confusing; combined gesture fires when slowest hand matches | Single hold_time for the combo unit |
| More than 2 hands | MediaPipe Hands max_num_hands above 2 degrades per-hand quality | Cap at 2 |

### UX Pattern: 2-Hand Binding Configuration

**Recommended UI flow (derived from VTubeStudio pattern, the industry reference for streamer gesture binding):**

When 2-hand mode is active in the Geral tab, the Gestos tab gains a second section below the existing single-hand bindings:

```
─────────────────────────────────────────
Gestos Combinados (2 mãos)
─────────────────────────────────────────
[+ Adicionar combinação]

Mão Esquerda      Mão Direita       Ação
[Dropdown ▼]  +  [Dropdown ▼]  →   [Ação ▼]
```

Each row is a combined binding: left-hand gesture dropdown + right-hand gesture dropdown + same action selector as single gestures (scene switch / hotkey / audio). No AND/OR toggle needed. Hold time and cooldown are shared fields at the section level, not per-row, matching the existing per-gesture parameter pattern.

The preview area shows when configuring: "Esquerda: Punho | Direita: Paz" in real time, making it easy to confirm the combo before saving.

### Pre-defined Useful Combined Gestures for Streamers

These are the gestures that matter for the streaming use case, based on OBS's most common streamer actions (scene switching, start/stop recording, mute, source toggle):

| Combo | Left Hand | Right Hand | Suggested Default Action |
|-------|-----------|------------|--------------------------|
| "Go live" signal | Mão aberta (OPEN_PALM) | Mão aberta (OPEN_PALM) | Iniciar transmissão / Trocar para cena ao vivo |
| "Encerrar" | Punho (FIST) | Punho (FIST) | Parar transmissão / Cena de encerramento |
| "BRB" | Punho (FIST) | Mão aberta (OPEN_PALM) | Trocar para cena "Volto já" |
| "Aprovação / Celebrar" | Joinha (THUMBS_UP) | Joinha (THUMBS_UP) | Tocar som de vitória / Overlay de comemoração |
| "Gravar + confirmar" | Punho (FIST) | Joinha (THUMBS_UP) | Iniciar gravação local |
| "Câmera off" | L (L_SHAPE) | L (L_SHAPE) | Ocultar fonte webcam |

These 6 pre-defined combos appear as selectable presets in the UI (user can pick a preset or build a custom one from scratch). Pre-defined combos populate the dropdowns automatically; the user can then override the action.

### MediaPipe Handedness: Technical Constraints

**Flip requirement:** The frame passed to MediaPipe must be `cv2.flip(frame, 1)` (horizontal flip) for `multi_handedness` labels to be correct. Verify this in `core/hand_tracker.py` — the existing code passes `frame_rgb` from the engine loop; the flip must happen before RGB conversion, not after.

**Position-based fallback logic:**
```
centroid_x = mean(landmark.x for landmark in hand_landmarks.landmark)
# In a mirrored (flipped) frame: centroid_x < 0.5 → user's left hand
# (appears on left side of the mirror image, which is the user's left)
inferred_side = "Left" if centroid_x < 0.5 else "Right"
```

Use `multi_handedness[i].classification[0].label` as the primary, position-based inference as tie-breaker when confidence < 0.75.

**Stability via existing GestureStabilityMonitor:** Apply the same majority-vote window to the combined gesture pair `(left_gesture, right_gesture)` as a tuple, not to each hand independently. This naturally handles the edge cases where one hand momentarily misclassifies.

### Complexity Estimate

| Sub-feature | Estimate | Risk |
|-------------|----------|------|
| Mode toggle (GES-01) + max_num_hands=2 | Low | Low |
| Multi-hand preview overlay (GES-02) | Low | Low |
| Config schema extension for combined bindings (GES-06) | Low | Low |
| Gestos tab section for combined bindings (GES-03, GES-04) | Medium | Medium (UI only) |
| Combined gesture detection + stability + cooldown (GES-05) | Medium | Medium — GestureStabilityMonitor refactor |
| Handedness flip audit + position-based fallback | Low | Low (one file: hand_tracker.py) |
| Pre-defined combos as UI presets | Low | Low |

---

## Section 3 — Preview UX (Carry-over from v1.1)

These features remain Active in PROJECT.md and are unchanged from v1.1 research. Listed here for completeness and to clarify scope.

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Gesture name overlay on live preview | Users must confirm what the app "sees" | Low | Draw on OpenCV frame before frame_ready.emit() |
| Hold-time progress bar in preview | Users need to learn the timing | Low | Horizontal bar overlay, fills yellow→green |
| Flash / highlight when action fires | Confirms action was triggered | Low | 1-frame green flash or text overlay |

### Differentiators for 2-Hand Mode

When 2-hand mode is active, the preview must show per-hand state:

```
[Esquerda: Punho ▓▓▓░░░]   [Direita: Paz ▓▓▓▓▓░]
```

Both progress bars fill simultaneously; the combined action only fires when both reach 100% of their shared hold_time. This is the single most important UX piece for the 2-hand feature — without it, users cannot understand why the combo is or is not firing.

---

## Section 4 — UX & UI Polish (Carry-over from v1.1)

Brief categorization — these are implementation items, not research questions.

### Table Stakes

| Feature | Complexity | Dependency |
|---------|------------|------------|
| Inline field validation (UX-08: wav file not found, hotkey invalid) | Low | None |
| First-run onboarding checklist (UX-09) | Low | Health indicators must be stable first |
| Consistent color palette across tabs (UI-01) | Low | None |
| Dark mode default (UI-02) | Low | None |

### Anti-Features

| Anti-Feature | Why Avoid |
|--------------|-----------|
| Full multi-step wizard (vs checklist) | Over-engineering for a tool with 3 tabs |
| Per-tab dark/light mode toggle | Inconsistency is worse than always-dark |
| Animated transitions between tabs | Performance cost; not a game UI |

---

## Section 5 — Platform Abstraction (Carry-over from v1.1)

Code quality feature, not user-facing. No research needed — this is pure refactor.

| Requirement | Complexity | Notes |
|-------------|------------|-------|
| PLT-01: Windows-specific imports behind platform/_windows.py | Medium | Mechanical refactor; test on each move |
| PLT-02: ActionManager receives AudioBackend + InputBackend | Medium | Dependency injection pattern |
| PLT-03: protocol.py defines interfaces | Low | Abstract base classes or Protocol |

---

## Feature Dependencies

```
GES-01 (mode toggle + max_num_hands=2)
  → GES-02 (multi-hand preview — must know mode to render)
  → GES-03/04 (combined binding UI — section only shows in 2-hand mode)
    → GES-05 (combined gesture detection — must have bindings schema first)
      → GES-06 (config schema extension — must precede detection logic)

CAM-05 → REMOVE (MSMF path is counterproductive)
CAM-06 → DEFER to v2.0 (driver constraint unsolvable without external software)
CAM-07 (lag measurement) → can ship independently as passive badge

UX-05/06 (preview overlay — single-hand)
  → 2-hand preview extension — natural follow-on once single-hand overlay exists

PLT-01/02/03 → independent; no feature dependency; prefer late in milestone to minimize merge conflicts
```

---

## MVP Recommendation for v1.2

**Priority order:**

1. **Combined gesture detection engine** (GES-01, GES-02, GES-05, GES-06) — core feature, must ship
2. **Combined gesture binding UI** (GES-03, GES-04 + pre-defined combos) — usability gate; engine alone is useless without UI
3. **Preview overlay** (UX-05, UX-06) + 2-hand variant — the feature feels complete only with this feedback
4. **Latency badge** (CAM-07 revised) — passive, low-effort, high trust signal
5. **UI polish + onboarding** (UX-07–09, UI-01–04) — can ship last without blocking above
6. **Platform abstraction** (PLT-01–03) — ship last; most disruptive refactor

**Defer:**
- CAM-05 (MSMF test): Remove from requirements — wrong solution
- CAM-06 (virtual cam internal loop): Defer to v2.0 — driver constraint
- AND/OR hand activation logic: Not needed for v1.2
- Temporal gesture sequences: v2.0 roadmap

---

## Sources

- OpenCV MSMF vs DirectShow latency: [GitHub issue #27917](https://github.com/opencv/opencv/issues/27917), [GitHub issue #17687](https://github.com/opencv/opencv/issues/17687), [OpenCV forum thread](https://forum.opencv.org/t/cv-cap-dshow-cv-cap-msmf-what-is-different/8254) — confidence LOW (web)
- pyvirtualcam Windows backend constraints: [PyPI page](https://pypi.org/project/pyvirtualcam/), [GitHub repo](https://github.com/letmaik/pyvirtualcam), [API docs](https://letmaik.github.io/pyvirtualcam/), [OBS issue #9680](https://github.com/obsproject/obs-studio/issues/9680) — confidence LOW (web)
- MediaPipe handedness API and mirror assumption: [MediaPipe docs](https://mediapipe.readthedocs.io/en/latest/solutions/hands.html) — confidence MEDIUM (context7/curated)
- MediaPipe handedness reliability issues: [GitHub issue #3047](https://github.com/google/mediapipe/issues/3047) — confidence LOW (web)
- VTubeStudio 2-hand gesture UX pattern: [VTubeStudio wiki](https://github.com/DenchiSoft/VTubeStudio/wiki/Hand-Tracking) — confidence LOW (web)
- OBS streamer hotkey actions: [OBS forum](https://obsproject.com/forum/threads/hotkeys-for-scene-scene-switch.19508/), [shortcut guides](https://www.eachnineteachnine.com/post/obs-keyboard-shortcuts-the-ultimate-guide-to-faster-streaming) — confidence LOW (web)
- Threaded capture for latency: [PyImageSearch](https://pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/) — confidence LOW (web)
- Status indicator UX principles: [Nielsen Norman Group](https://www.nngroup.com/articles/indicators-validations-notifications/) — confidence MEDIUM (industry standard)
- Codebase: `core/camera.py`, `core/hand_tracker.py`, `engine/gesture_engine.py`, `config.json`, `.planning/PROJECT.md` — confidence HIGH (direct inspection)
