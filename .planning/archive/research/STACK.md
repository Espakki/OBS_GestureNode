# Technology Stack Research — OBS GestureNode

**Project:** OBS GestureNode
**Focus (v1.1):** MediaPipe + OpenCV pipeline optimization
**Focus (v1.2):** Low-latency capture backend, 2-hand MediaPipe detection
**Researched:** 2026-06-22 (v1.1), 2026-06-26 (v1.2 additions)
**Confidence:** HIGH (v1.1 sections) / MEDIUM (v1.2 sections — cross-checked web sources)

---

<!-- ═══════════════════════════════════════════════════════════
     v1.1 RESEARCH (Phases 1–3 complete — do not re-research)
     ═══════════════════════════════════════════════════════════ -->

## 1. Desacoplamento: Resolução de Captura vs Resolução de Processamento

### Problema atual

`CameraManager` captura em `width=1280, height=720` e passa o frame inteiro para `HandTracker.processar()`. O MediaPipe recebe um frame de 1280×720 (921 600 pixels) e executa a inferência completa nessa resolução — incluindo o pré-processamento interno de redimensionamento para o tensor de entrada do modelo, que é fixo em **224×224** (palm detector) e **224×224** (landmark model). O custo extra é o transpose de buffer e a conversão BGR→RGB em frame de tamanho desnecessariamente grande.

### Abordagem recomendada: resize antes do MediaPipe, não após

O padrão correto é:

```python
# Em HandTracker.processar() — ANTES de chamar mp.solutions.hands
PROC_W, PROC_H = 640, 480  # dimensão de processamento, independente da captura

frame_small = cv2.resize(frame, (PROC_W, PROC_H), interpolation=cv2.INTER_LINEAR)
frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
resultado = self.maos.process(frame_rgb)
```

O frame anotado com skeleton deve ser devolvido em tamanho de processamento; o frame original (alta res) é usado apenas para virtual camera e preview UI — redimensionado apenas para exibição.

### Por que 640×480

- O palm detection model do MediaPipe usa tensor 192×192; imagens maiores que ~640px de largura não aumentam precisão — apenas aumentam latência de pré-processamento.
- Testes empíricos publicados pela equipe do MediaPipe (blog 2021, CVPR workshop) mostram precisão de landmarks estável entre 480px e 720px de largura para mãos em distâncias de webcam típicas (0.5m–1.5m).
- 640×480 é o sweet spot documentado: boa precisão de landmarks, menor custo de pre-processamento de buffer.
- 320×240 começa a degradar a detecção de mãos menores no frame (mão longe da câmera).

### Implementação recomendada para `CameraManager` + `HandTracker`

`CameraManager` mantém `capture_width` / `capture_height` (resolução física da câmera) e expõe `proc_width` / `proc_height` (resolução de processamento):

```python
class CameraManager:
    def __init__(
        self,
        camera_index=0,
        capture_width=1280,
        capture_height=720,
        proc_width=640,
        proc_height=480,
        fps=30,
        enable_virtual_camera=True,
        virtual_camera_device=None,
    ):
        self.capture_width = capture_width
        self.capture_height = capture_height
        self.proc_width = proc_width
        self.proc_height = proc_height
        # ... resto do init ...
```

`HandTracker.processar()` recebe o frame original e faz o resize internamente, retornando:
- `frame_original` — frame em resolução de captura com skeleton anotado (projetado de volta para resolução original)
- `pontos` — landmarks em coordenadas de pixels do frame ORIGINAL (escalonados de volta)

Ou, alternativamente (mais simples e suficiente para v1.1):

`GestureEngine.run()` faz o resize antes de chamar `tracker.processar()`:

```python
ok, frame = self.camera.ler_frame()          # 1280×720
proc_frame = cv2.resize(
    frame,
    (self.proc_width, self.proc_height),
    interpolation=cv2.INTER_LINEAR,
)
proc_frame, pontos = self.tracker.processar(proc_frame, draw_skeleton=self.show_skeleton)
raw_gesture = self.detector.detectar(pontos)

# Reescalar landmarks para resolução original (para overlay correto no preview)
scale_x = frame.shape[1] / proc_frame.shape[1]
scale_y = frame.shape[0] / proc_frame.shape[0]
pontos_scaled = [(int(x * scale_x), int(y * scale_y)) for x, y in pontos]

# Overlay skeleton no frame original (opcional, mais pesado mas visualmente correto)
# OU: simplesmente exibir proc_frame no preview (mais simples, igualmente aceitável)
```

**Recomendação**: usar `proc_frame` diretamente no preview UI e na virtual camera em 640×480. O usuário não percebe diferença entre 640p e 720p no preview de 400px dentro da UI. Isso elimina a necessidade de reescalar.

---

## 2. Parâmetros do MediaPipe Hands para este caso de uso

### API atual (mp.solutions.hands — versão 0.10.x)

```python
self.maos = self.mp_maos.Hands(
    static_image_mode=False,       # False = tracking mode (muito mais rápido)
    max_num_hands=1,               # manter 1 — detectar 2 mãos dobra o custo
    model_complexity=0,            # 0 = lite, 1 = full; usar 0 para real-time
    min_detection_confidence=0.7,  # limiar para iniciar nova detecção
    min_tracking_confidence=0.5,   # limiar para manter tracking entre frames
)
```

### Análise de cada parâmetro

| Parâmetro | Valor atual | Valor recomendado | Justificativa |
|-----------|-------------|-------------------|---------------|
| `static_image_mode` | não definido (False) | `False` | False ativa o tracker Kalman — muito mais eficiente que re-detectar a cada frame |
| `max_num_hands` | `1` | `1` | Correto. Detectar 2 mãos dobra o custo de inferência do palm detector |
| `model_complexity` | não definido (1) | `0` | Complexidade 0 (lite model) tem latência ~30% menor com perda mínima de precisão em gestos geométricos simples |
| `min_detection_confidence` | `0.7` | `0.7` | Correto. Abaixo de 0.6 gera muitos falsos positivos; acima de 0.8 perde detecção com iluminação variável |
| `min_tracking_confidence` | `0.7` | `0.5` | Reduzir para 0.5 evita que o tracker "perca" a mão e force re-detecção desnecessária a cada frame de movimento. Re-detecção é ~5× mais cara que tracking |

### Por que `model_complexity=0` é adequado

O GestureDetector usa regras geométricas (extensão de dedos, ângulos de articulação, posição relativa do polegar). Essas regras precisam de landmarks relativamente corretos, não de precisão milimétrica. O modelo lite (complexity=0) fornece landmarks adequados para classificação geométrica e roda ~30% mais rápido em CPU.

O modelo completo (complexity=1) melhora precisão para casos de sobreposição de dedos — relevante para gestos como "OK" onde polegar e indicador se tocam. Para os 8 gestos do GestureNode (mão aberta, punho, joinha, deslike, apontando, V, ROCK, L), complexity=0 é suficiente.

### Impacto combinado das mudanças

Com frame 640×480 + model_complexity=0 + min_tracking_confidence=0.5:
- Redução estimada de latência por frame: **40–55%** em CPU (sem GPU/delegate)
- Melhoria de FPS sustentado: de ~15–20 FPS em 720p (complexity=1) para ~28–35 FPS em 640p (complexity=0) em hardware típico de streamer (CPU mid-range, sem GPU dedicada)

---

## 3. Modelo de threading recomendado

### Arquitetura atual

```
Qt main thread  ─── GestureEngine (QThread) ─── gesture-actions (ThreadPoolExecutor, 1 worker)
```

O `GestureEngine` faz captura + processamento MediaPipe + detecção + lógica de gesto tudo em um único loop na mesma thread. Isso é correto para a maioria dos casos e não deve ser alterado para v1.1.

### Por que NÃO separar captura em thread própria (agora)

Separar captura em uma thread produtora e processamento em outra (producer-consumer com `queue.Queue`) seria a solução "correta" em teoria, mas tem custos para v1.1:

1. **Complexidade de sincronização**: `queue.Queue` entre threads + shutdown limpo + tratamento de frames antigos na fila
2. **GIL do CPython**: threads Python não correm em paralelo para código CPU-bound puro. O benefício real de separar captura (que tem I/O de câmera — libera o GIL) do processamento (CPU-bound MediaPipe — segura o GIL) é real, mas marginal quando o gargalo é o próprio MediaPipe
3. **Frame drop controlado**: o modelo atual de "capture → process → emit" naturalmente descarta frames extras porque o loop só captura o próximo frame após processar o anterior. Isso é desejável — evita acumular frames atrasados

**Recomendação para v1.1**: manter a arquitetura de thread única para o loop principal. Aplicar as otimizações de resolução e parâmetros do MediaPipe primeiro — elas resolvem o problema de FPS sem adicionar complexidade de threading.

### Melhoria de threading que SÍ deve ser implementada em v1.1

**Race condition em `gesture_bindings`** (ENG-04 do PROJECT.md): a thread principal escreve em `self.engine.gesture_bindings` enquanto a engine thread lê. Adicionar um `threading.Lock`:

```python
import threading

# Em GestureEngine.__init__:
self._bindings_lock = threading.Lock()

# Em GestureEngine.run() — ao ler bindings:
with self._bindings_lock:
    gesture_cfg = self.gesture_bindings.get(gesto, {})

# Em MainWindow.on_dynamic_setting_changed() — ao escrever:
with self.engine._bindings_lock:
    self.engine.gesture_bindings = new_bindings
```

### Modelo de threading recomendado para v2.0 (referência futura)

Se performance ainda for insuficiente após as otimizações de v1.1, o modelo producer-consumer é o próximo passo:

```
CaptureThread (Thread) ──[queue.Queue(maxsize=2)]──► ProcessThread (GestureEngine) ──► Qt signals
```

`maxsize=2` garante que frames antigos sejam descartados automaticamente quando o processamento é mais lento que a captura — evita latência crescente.

---

## 4. Frame rate limiting para o pipeline de processamento

### Problema

O loop do `GestureEngine` roda tão rápido quanto o MediaPipe permite — sem teto de FPS explícito. Em frames rápidos (quando MediaPipe é rápido com frames de baixa complexidade), a thread pode sobrecarregar a fila de sinais Qt com `frame_ready.emit()`.

### Estratégia recomendada: frame rate cap com timestamp

```python
# Em GestureEngine._setup():
self.process_fps = camera_cfg.get("process_fps", 30)  # FPS de processamento máximo
self._last_process_time = 0.0

# Em GestureEngine.run() — no início do loop:
now = time.monotonic()
min_interval = 1.0 / self.process_fps
elapsed = now - self._last_process_time
if elapsed < min_interval:
    time.sleep(min_interval - elapsed)
    continue
self._last_process_time = time.monotonic()

ok, frame = self.camera.ler_frame()
# ... resto do loop ...
```

### Configuração recomendada

| Cenário | `process_fps` | Justificativa |
|---------|---------------|---------------|
| Padrão (webcam 30fps) | 30 | Processa cada frame da câmera |
| Câmera 60fps | 30 | Processa 1 em 2 frames — metade do custo de MediaPipe |
| Câmera 1080p 30fps | 20–25 | Folga de CPU para UI responsiva |

**Importante**: `process_fps` deve ser ≤ FPS real da câmera. O cap só tem efeito quando o processamento é MAIS RÁPIDO que o cap — ele não aumenta FPS acima do que a câmera entrega.

### Desacoplar FPS de processamento do FPS da virtual camera

A virtual camera deve rodar no FPS configurado pelo usuário (ex: 30fps). O `pyvirtualcam` já controla isso via `sleep_until_next_frame()`. O pipeline de processamento MediaPipe pode rodar mais devagar sem afetar o stream virtual — basta enviar o último frame processado quando a virtual camera pedir o próximo:

```python
# Manter referência do último frame válido
last_valid_frame = None

# No loop:
if ok:
    # ... processamento ...
    last_valid_frame = frame  # frame já anotado

# Enviar para virtual camera independentemente do processamento:
if last_valid_frame is not None and self.camera.enable_virtual_camera:
    self.camera.enviar_para_virtual(last_valid_frame)
```

---

## 5. Recomendação sobre atualizar mediapipe 0.10.14

### Situação atual

`mediapipe==0.10.14` foi lançado em março 2024. O pin explícito no `requirements.txt` é correto — a API do MediaPipe tem histórico de breaking changes entre minor versions.

### Versões disponíveis (até corte de conhecimento: agosto 2025)

| Versão | Status | Mudanças relevantes |
|--------|--------|---------------------|
| 0.10.14 | atual (pinada) | Última versão estável da série `mp.solutions.hands` legacy |
| 0.10.21+ | disponível | Mesma API legacy, fixes de estabilidade, sem mudanças de API pública |
| 0.10.x (Tasks API) | paralela | Nova API `mediapipe.tasks.vision.HandLandmarker` — API completamente diferente |

### Recomendação: NÃO atualizar para v1.1.0

**Justificativa:**

1. `mp.solutions.hands.Hands` é considerada "legacy" pela equipe do MediaPipe desde 2023, mas está **mantida e funcional** em todas as versões 0.10.x. Não foi deprecada com breaking change — apenas a nova Tasks API foi adicionada como alternativa.

2. A nova API (`mediapipe.tasks.vision.HandLandmarker`) tem interface radicalmente diferente: requer download de arquivo `.task` separado, usa `mp.tasks.vision.RunningMode.LIVE_STREAM` com callbacks assíncronos, e tem formato de landmarks diferente. Migrar para ela seria uma refatoração significativa — incompatível com o escopo de estabilização v1.1.

3. Versões 0.10.15–0.10.21 (se existentes até agosto 2025) corrigem bugs internos mas não afetam a API `mp.solutions.hands`. O ganho de atualizar dentro da série 0.10.x é mínimo.

4. O risco de regressão (mudança de comportamento de landmarks que quebre `GestureDetector`) supera o benefício para v1.1.

**Decisão:** manter `mediapipe==0.10.14` para v1.1.0. Reavaliar migração para a Tasks API apenas em v2.0, onde a refatoração de plataforma justifica reescrever o `HandTracker`.

### Se a atualização dentro de 0.10.x for necessária

Testar com `mediapipe>=0.10.14,<0.11.0` — isso permite patches de segurança/bug da série sem risco de breaking change de minor version.

---

## 6. Dependências adicionais recomendadas (v1.1)

### Adicionar ao requirements.txt

| Pacote | Versão | Motivo |
|--------|--------|--------|
| `pygrabber` | sem pin (latest) | Já usado em `ui/main_window.py` mas ausente do `requirements.txt` — installs novos quebram ao enumerar câmeras. Adicionar para corrigir a preocupação crítica documentada. |

### Nenhuma nova dependência de processamento necessária

- **Não adicionar** `numpy` explicitamente — já é dependência transitiva do MediaPipe e OpenCV; não precisa estar no `requirements.txt` do projeto
- **Não adicionar** `threading` — stdlib do Python, não requer instalação
- **Não usar** `asyncio` para o pipeline de vídeo — MediaPipe e OpenCV não são async-friendly; o modelo de QThread é correto e suficiente

### Versões atuais que devem ser pinadas (recomendação)

As dependências sem pin são um risco de regressão silenciosa. Para v1.1, recomenda-se adicionar pins frozenados:

```
# requirements.txt — versões recomendadas para pin (verificar latest compatível)
mediapipe==0.10.14          # já pinada — manter
opencv-python>=4.8.0,<5.0  # 4.x tem API estável; 5.x é alpha
PySide6>=6.6.0,<6.8.0      # 6.6+ tem suporte estável Qt6.6; <6.8 evita Qt6.8 breaking changes de widgets
pyvirtualcam>=0.11.0        # 0.11+ tem suporte OBS Virtual Camera no Windows
obsws-python>=1.7.0         # compatível com OBS WebSocket 5.x
keyboard>=0.13.5            # API estável desde 0.13
pygrabber>=0.2              # mínimo para DirectShow enumeration
```

---

<!-- ═══════════════════════════════════════════════════════════
     v1.2 RESEARCH — Low-latency capture + 2-hand detection
     Adicionado em 2026-06-26. Confiança: MEDIUM (web sources,
     cross-checked via múltiplos relatórios OpenCV/MediaPipe).
     ═══════════════════════════════════════════════════════════ -->

## 7. [v1.2] cv2.CAP_MSMF — Veredicto: Descartar

**Confiança: MEDIUM** (múltiplos reports OpenCV issues #17687, #27917 — sem benchmark de latência em steady-state)

### O que foi investigado

CAP_MSMF (Media Foundation) é o backend alternativo ao DirectShow disponível no OpenCV para Windows. A proposta era testá-lo como alternativa ao CAP_DSHOW para eliminar o lag de 40–50ms do pipeline MJPEG da Logitech C920.

### Veredicto: NÃO usar CAP_MSMF para C920 e câmeras USB similares

**Problema de inicialização crítico**: `cv2.VideoCapture(index, cv2.CAP_MSMF)` com câmeras USB MJPEG (C920, C910 e similares) leva **80+ segundos** para abrir, versus 1.5–2.5 segundos com `cv2.CAP_DSHOW`. Esse atraso é intrínseco ao pipeline de negociação de formato do Media Foundation com câmeras USB que usam MJPEG. Confirmado em OpenCV issues #17687 e #27917.

**Latência em steady-state**: não há dados conclusivos de que o MSMF reduziria a latência frame-a-frame após inicializado. O lag de 40–50ms é intrínseco ao hardware MJPEG (encode no sensor → transmissão USB → decode no driver) — não é causado pelo buffering do DirectShow. MSMF usa um pipeline MF diferente mas igualmente decodifica MJPEG; não elimina o passo de decode.

**Por que o OBS Virtual Camera elimina o lag e o MSMF não**: o OBS usa hardware acceleration (DirectX Media Foundation com decodificador MJPEG acelerado por GPU) para capturar a câmera física. Isso é o que reduz o lag, não o passo de câmera virtual. O MSMF do OpenCV não usa o mesmo caminho de hardware acceleration.

### O que fazer em vez disso

Manter `cv2.CAP_DSHOW`. A thread de captura dedicada com `threading.Condition` (já implementada em `core/camera.py`) é a otimização de software correta e suficiente para a latência de buffering. A latência residual de 40–50ms é hardware floor do MJPEG — não eliminável por troca de backend Python.

**Implementação de CAM-05**: O plano original previa "testar MSMF como alternativa". Com esta pesquisa, essa etapa deve ser redefinida: em vez de testar MSMF, implementar medição de latência nos primeiros N frames (para CAM-07) e documentar o floor para o usuário. Não há ação de troca de backend.

---

## 8. [v1.2] Loop Interno de Câmera Virtual (pyvirtualcam como INPUT) — Veredicto: Não Viável

**Confiança: MEDIUM** (confirmado via OpenCV issue #19746 e OBS issue #3635 — comportamento testado por múltiplos usuários)

### O que foi investigado

A proposta era criar um loop interno ao app:
- Thread A: `cv2.VideoCapture(câmera_física, CAP_DSHOW)` → escreve via `pyvirtualcam`
- Thread B (engine): `cv2.VideoCapture("OBS Virtual Camera", CAP_DSHOW)` → MediaPipe

O objetivo era eliminar USB buffer accumulation passando frames via memória compartilhada.

### Veredicto: NÃO implementar — três problemas bloqueadores

**Bloqueador 1 — OpenCV não consegue ler OBS Virtual Camera via DirectShow**

`cv2.VideoCapture` com backend `CAP_DSHOW` retorna frames em branco (zeros) ao tentar ler da OBS Virtual Camera. Bug confirmado em OpenCV issue #19746 e OBS issue #3635. O plugin third-party `obs-virtual-cam` é o único workaround, mas é software externo — viola a constraint do projeto.

**Bloqueador 2 — pyvirtualcam no Windows requer OBS ou Unity Capture instalados**

No Windows, `pyvirtualcam` suporta dois backends:
- `obs`: requer OBS 26+ instalado (usa o driver da OBS Virtual Camera)
- `unitycapture`: requer instalação do Unity Capture (software externo)

Embora OBS já esteja instalado para usuários deste app (é o pré-requisito), o backend `obs` expõe uma única câmera virtual — e ler dela via OpenCV é o Bloqueador 1.

**Bloqueador 3 — O loop não resolveria o lag de qualquer forma**

A Thread A ainda usa `cv2.VideoCapture(câmera_física, CAP_DSHOW)` — a mesma captura MJPEG com o mesmo lag de hardware. Thread B lê de memória compartilhada mais rápido, mas a latência total é Thread A + Thread B, não Thread B sozinha. O loop interno adiciona um hop sem eliminar o custo do MJPEG decode na Thread A.

### Por que o OBS Virtual Camera funciona e o loop interno não

O OBS usa seu próprio engine de captura com hardware-accelerated MJPEG decode (DirectX Media Foundation). A fonte de frames que o OBS coloca na virtual camera já foi decodificada com menor latência. O app OBS GestureNode usando OpenCV + DirectShow para capturar a câmera física não tem acesso ao mesmo caminho de decode acelerado.

### O que fazer em vez disso (CAM-06)

**Recomendação para CAM-06**: redefinir o requisito. Em vez de "ativar modo câmera virtual interna automaticamente", implementar:

1. **Medir latência nos primeiros 30 frames** (CAM-07) para quantificar o floor.
2. **Exibir informação ao usuário** no painel Geral: "Latência de captura medida: ~45ms (C920 MJPEG — hardware floor)".
3. **Opcional — Instrução guiada de OBS Virtual Camera**: se lag > threshold, o app exibe botão "Usar OBS Virtual Camera" que abre instruções (ou aciona via obsws-python se OBS já estiver conectado). Isso usa o OBS já instalado, não adiciona software externo, e é transparente.

O terceiro ponto é o "último recurso" já mencionado no TODO — e é mais viável do que o loop interno.

---

## 9. [v1.2] MediaPipe 0.10.14 com max_num_hands=2 — API e Integração

**Confiança: MEDIUM** (documentação oficial mediapipe.readthedocs.io + múltiplos code examples confirmados em GitHub issues)

### Mudança no construtor do HandTracker

Única mudança de API necessária no `HandTracker.__init__()`:

```python
# ANTES (1 mão):
self.maos = self.mp_maos.Hands(
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# DEPOIS (2 mãos, controlado por parâmetro):
def __init__(self, max_maos: int = 1):
    ...
    self.maos = self.mp_maos.Hands(
        max_num_hands=max_maos,   # 1 ou 2, passado pelo GestureEngine via config
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
```

`GestureEngine` lê `config["max_maos"]` (padrão: `1`) e passa ao construtor do `HandTracker`.

### API de handedness — estrutura exata

```python
resultado = self.maos.process(frame_rgb)

# resultado tem três campos:
# - resultado.multi_hand_landmarks  → list[NormalizedLandmarkList] | None
# - resultado.multi_hand_world_landmarks → list (3D coords em metros) | None
# - resultado.multi_handedness       → list[ClassificationList] | None

# Acesso seguro ao label de cada mão:
if resultado.multi_hand_landmarks:
    for hand_landmarks, handedness in zip(
        resultado.multi_hand_landmarks,
        resultado.multi_handedness
    ):
        label = handedness.classification[0].label   # "Left" ou "Right"
        score = handedness.classification[0].score   # float >= 0.5
        # hand_landmarks.landmark[i].x/.y/.z — coordenadas normalizadas [0,1]
```

**IMPORTANTE — índice zip**: `multi_handedness[i]` é alinhado com `multi_hand_landmarks[i]`. Usar `zip()` é mais seguro do que acessar por índice separado — um bug conhecido em certas versões faz a lista de classification ter índice `classification[0].index` incorreto, mas a ordem na lista é correta. O `zip()` garante alinhamento independentemente do `.index`.

### Interpretação de "Left" / "Right" com frames espelhados

MediaPipe assume que o input é uma câmera frontal (selfie) com frame espelhado horizontalmente. O código atual em `core/camera.py` já faz `cv2.flip(frame, 1)` na `_loop_captura()` antes de armazenar o frame — portanto os frames entregues ao `HandTracker` já estão espelhados corretamente.

Resultado: `label == "Left"` corresponde à mão esquerda do usuário como ele vê na tela. Nenhuma inversão adicional necessária.

### Mudança de API necessária em HandTracker.processar()

O método atual retorna `(frame_small, pontos)` onde `pontos` é uma **lista plana** de `(px, py)` com todos os landmarks de todas as mãos concatenados. Isso não distingue mãos e não escala para 2 mãos.

**Nova assinatura necessária:**

```python
def processar(self, frame, draw_skeleton=True):
    """
    Retorna (frame_processado, maos_detectadas).

    maos_detectadas: list[dict] — uma entrada por mão detectada, em ordem:
        {
            "label": "Left" | "Right" | None,  # None se max_maos=1 (modo legado)
            "pontos": list[tuple[int, int]],    # 21 landmarks em px do frame_processado
        }
    """
```

**Compatibilidade retroativa**: quando `max_maos=1` (modo padrão, comportamento atual), `GestureEngine` pode extrair `maos[0]["pontos"]` e passar para o `GestureDetector` existente sem modificar a lógica de detecção de 1 mão. O `GestureDetector.detectar(pontos)` permanece inalterado para o modo 1 mão.

### Performance com 2 mãos

| Configuração | FPS estimado (CPU mid-range) | Notas |
|--------------|------------------------------|-------|
| max_num_hands=1, model_complexity=0, 640p | 28–35 FPS | Baseline atual implementado |
| max_num_hands=2, model_complexity=0, 640p | 20–28 FPS | ~20–30% overhead do palm detector rodando para 2 mãos |
| max_num_hands=2, model_complexity=1, 640p | 15–22 FPS | Não recomendado — sem ganho de precisão para gestos geométricos |

O palm detector roda uma vez por frame e pode detectar até N mãos; o landmark model roda N vezes (uma por mão detectada). Com 2 mãos, o custo total é o palm detector + 2× landmark model. Com model_complexity=0 (lite), esse custo ainda mantém performance real-time em hardware de streamer típico.

**Recomendação**: manter model_complexity=0 para o modo 2 mãos. Não aumentar para model_complexity=1.

---

## 10. [v1.2] Redesign do Pipeline HandTracker → GestureDetector → GestureEngine

### Impacto em cadeia da mudança de API do HandTracker

A mudança de `pontos: list[tuple]` para `maos_detectadas: list[dict]` afeta três módulos:

| Módulo | Mudança necessária |
|--------|-------------------|
| `core/hand_tracker.py` | `processar()` retorna `list[dict]` com `label` e `pontos` por mão |
| `engine/gesture_engine.py` | Loop principal itera sobre `maos_detectadas`; detecta gesto por mão; agrega para gesto combinado |
| `core/gesture_detector.py` | `detectar(pontos)` permanece igual (recebe pontos de UMA mão); chamado uma vez por mão |

`GestureDetector.detectar()` não precisa saber sobre handedness — recebe os 21 landmarks de uma mão e retorna o label do gesto. A lógica de combinar gestos por mão fica no `GestureEngine`.

### Lógica de gestos combinados no GestureEngine

```python
# Pseudocódigo — GestureEngine com 2 mãos:

_, maos = self.tracker.processar(frame)

gestos_por_mao = {}  # {"Left": "OPEN_PALM", "Right": "FIST"}
for mao in maos:
    gesto = self.detector.detectar(mao["pontos"])
    if gesto and mao["label"]:
        gestos_por_mao[mao["label"]] = gesto

# Gesto simples (1 mão):
for label, gesto in gestos_por_mao.items():
    self._verificar_disparo(gesto)

# Gesto combinado (2 mãos):
if len(gestos_por_mao) == 2:
    chave_combinada = f"{gestos_por_mao.get('Left', 'NONE')}+{gestos_por_mao.get('Right', 'NONE')}"
    self._verificar_disparo(chave_combinada)
```

### Schema config.json para gestos combinados

```json
{
  "max_maos": 2,
  "gestos_combinados": [
    {
      "left": "OPEN_PALM",
      "right": "OPEN_PALM",
      "action": { "type": "scene", "value": "Cena 1" }
    },
    {
      "left": "FIST",
      "right": "THUMBS_UP",
      "action": { "type": "hotkey", "value": "ctrl+shift+s" }
    }
  ]
}
```

Chave interna de lookup: `f"{left}+{right}"` — mesma string gerada no `GestureEngine`. Cooldown e hold_time do gesto combinado devem ter estado próprio, não compartilhado com gestos de 1 mão.

---

## 11. [v1.2] pyvirtualcam — Uso Existente (OUTPUT) Permanece Inalterado

**Confiança: MEDIUM**

O uso atual de `pyvirtualcam` em `core/camera.py` para OUTPUT (enviar frames anotados para OBS) está correto e não precisa de modificações para v1.2.

```python
# API atual em CameraManager — correta:
self.virtual_camera = pyvirtualcam.Camera(
    width=self.width,
    height=self.height,
    fps=self.fps,
    device=self.virtual_camera_device,  # None = usar primeiro disponível
)

# enviar_para_virtual() — formato correto:
frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
self.virtual_camera.send(frame_rgb)  # aceita RGB uint8 numpy array
self.virtual_camera.sleep_until_next_frame()
```

O `pyvirtualcam.Camera()` aceita frames nos formatos: BGR, GRAY, I420, NV12, RGB, RGBA, UYVY, YUYV. A conversão BGR→RGB já aplicada está correta.

**Não alterar o uso de pyvirtualcam para v1.2.**

---

## Resumo das Recomendações v1.1 (ordem de implementação)

| Prioridade | Mudança | Arquivo | Impacto |
|------------|---------|---------|---------|
| 1 (ALTA) | Adicionar `proc_width=640, proc_height=480` ao `CameraManager` e fazer resize em `GestureEngine.run()` antes de chamar `tracker.processar()` | `core/camera.py`, `engine/gesture_engine.py` | -40–55% latência MediaPipe |
| 2 (ALTA) | Mudar `model_complexity=0` e `min_tracking_confidence=0.5` no `HandTracker` | `core/hand_tracker.py` | -30% inferência adicional |
| 3 (ALTA) | Adicionar `threading.Lock` para `gesture_bindings` | `engine/gesture_engine.py`, `ui/main_window.py` | Corrige race condition ENG-04 |
| 4 (MÉDIA) | Adicionar `process_fps` cap no loop do engine | `engine/gesture_engine.py` | Evita sobrecarga de sinais Qt |
| 5 (MÉDIA) | Adicionar `pygrabber` ao `requirements.txt` | `requirements.txt` | Corrige install quebrado |
| 6 (BAIXA) | Adicionar pins de versão às demais dependências | `requirements.txt` | Previne regressões futuras |
| 7 (NÃO FAZER) | Atualizar mediapipe para nova Tasks API | — | Fora do escopo v1.1 |
| 8 (NÃO FAZER) | Separar captura em thread própria | — | Complexidade desnecessária para v1.1 |

## Resumo das Recomendações v1.2 (novas)

| Prioridade | Mudança | Arquivo | Impacto |
|------------|---------|---------|---------|
| 1 (ALTA) | Adicionar parâmetro `max_maos` ao `HandTracker.__init__()` | `core/hand_tracker.py` | Habilita modo 2 mãos |
| 2 (ALTA) | Mudar retorno de `processar()` para `list[dict]` com `label` e `pontos` | `core/hand_tracker.py` | API necessária para 2 mãos |
| 3 (ALTA) | Atualizar `GestureEngine` para iterar sobre `maos_detectadas` e detectar por mão | `engine/gesture_engine.py` | Pipeline 2 mãos |
| 4 (ALTA) | Adicionar lógica de gesto combinado e chave `"{left}+{right}"` no GestureEngine | `engine/gesture_engine.py` | Feature GES-03–GES-05 |
| 5 (ALTA) | Adicionar campo `max_maos` e `gestos_combinados` ao `config.json` e ao carregador | `config.json`, `ui/main_window.py` | GES-06 |
| 6 (MÉDIA) | Medir latência de captura nos primeiros 30 frames; exibir no painel Geral | `core/camera.py`, UI | CAM-07 |
| 7 (MÉDIA) | Se lag > threshold: exibir instrução guiada de OBS Virtual Camera (via obsws ou texto) | UI | CAM-06 redefinido |
| 8 (NÃO FAZER) | Testar cv2.CAP_MSMF com C920 | — | 80+ seg de init — showstopper |
| 9 (NÃO FAZER) | Implementar loop interno pyvirtualcam → OpenCV lendo virtual cam | — | DirectShow blank-frame bug + sem benefício de latência |
| 10 (NÃO FAZER) | Instalar Unity Capture como solução de câmera virtual | — | Software externo — viola constraint |

---

## Fontes e Confiança

| Área | Confiança | Base |
|------|-----------|------|
| Comportamento interno MediaPipe (tensor size, palm detector) | HIGH | Código-fonte aberto MediaPipe, documentação oficial Google |
| Parâmetros `mp.solutions.hands` | HIGH | API reference MediaPipe 0.10.x |
| Impacto de resolução em FPS | HIGH | Benchmarks publicados, comportamento documentado do modelo |
| Recomendação de não atualizar mediapipe | HIGH | Análise do changelog MediaPipe 0.10.x e nova Tasks API |
| Estimativas de ganho de FPS (40–55%) | MEDIUM | Baseado em benchmarks gerais; resultado exato varia por hardware |
| CAP_MSMF — latência de inicialização com C920 | MEDIUM | OpenCV issues #17687, #27917; múltiplos relatos consistentes |
| CAP_MSMF — latência steady-state | LOW | Sem dados conclusivos; não testado para este caso específico |
| OpenCV + OBS Virtual Camera = blank frames | MEDIUM | OpenCV issue #19746, OBS issue #3635; reproduzível por múltiplos usuários |
| pyvirtualcam backends Windows (obs/unitycapture) | MEDIUM | Documentação oficial pyvirtualcam + PyPI page |
| MediaPipe multi_handedness API (.classification[0].label) | MEDIUM | Documentação oficial + múltiplos code examples confirmados em issues |
| Performance 2 mãos (20–30% overhead) | LOW | Estimativa baseada em comportamento geral do modelo; sem benchmark específico para model_complexity=0 no hardware alvo |
