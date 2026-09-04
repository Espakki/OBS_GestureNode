# Backlog

Itens abertos, em ordem de prioridade. Sem checkbox de progresso por decisão de projeto:
status vive só no [STATE.md](STATE.md). Quando um item fecha, ele sai daqui e vira uma
linha com SHA lá.

Tamanho: **P** = uma sessão curta · **M** = uma sessão · **G** = várias sessões, merece
plano em `active/`.

---

## Fase A — Fazer o app subir em ambiente limpo

Objetivo: `git clone` + `pip install -r requirements.txt` + `python main.py` funciona numa
máquina virgem. Hoje não funciona.

### B-01 · Declarar `av` (PyAV) no requirements · **P**

`core/camera.py` faz `import av` no topo, e a cadeia `main.py → ui/main_window → mixins →
engine → core.camera` é toda import de nível de módulo. Numa máquina limpa o app morre com
`ModuleNotFoundError: No module named 'av'` antes de desenhar a janela.

Entrou junto com a migração pro PyAV (`76607d8`), depois que a fase 1 já tinha fechado o
critério "pip install em ambiente limpo instala tudo" — o critério ficou verde no papel e a
dependência entrou depois.

Menor, mesma categoria: `integrations/obs_connect_thread.py` importa `websocket` direto.
Funciona de carona com o `obsws-python`, mas é transitiva não declarada.

**Arquivos:** `requirements.txt`
**Validar:** venv novo, `pip install -r requirements.txt`, `python main.py` abre.

### B-02 · Câmera virtual recebe upscale de 640px · **M**

No modo `automatico` o frame percorre: captura 1920×1080 → `HandTracker.processar()` reduz
pra `PROCESS_W=640` e **retorna o frame pequeno** → `gesture_engine` reatribui `frame` (o
1080p original é descartado) → `enviar_para_virtual()` vê que não bate com a resolução alvo
e **faz upscale de volta pra 1080p**.

O OBS recebe 640p esticado, não a captura nativa — com o esqueleto desenhado por cima se
`show_skeleton` estiver ligado. Paga-se o custo de capturar em 1080p pra entregar 640p.

O downscale pra inferência está certo (normaliza custo do MediaPipe). O problema é o frame
de inferência ter virado também o frame de saída: são dois consumidores com necessidades
opostas — a inferência quer pequeno, a câmera virtual quer nativo.

**Decidir antes de codar:** o que a VCam deve entregar? Frame nativo limpo, ou nativo com
esqueleto (exige escalar os landmarks de volta)? Ver [DECISIONS.md](DECISIONS.md) D-09.

**Arquivos:** `core/hand_tracker.py`, `engine/gesture_engine.py`, `core/camera.py`

### B-03 · Validar o `main.spec` contra as deps atuais · **M**

O spec é de maio, quando não havia PyAV nem pygrabber. Tem `hiddenimports=[]` e só
`collect_all('mediapipe')`. PyAV traz DLLs do FFmpeg; `pygrabber` usa `comtypes`, que gera
módulos em runtime — os dois são historicamente problemáticos no PyInstaller.

Não dá pra afirmar que quebra sem rodar. Validar cedo, não na véspera de distribuir.

**Arquivos:** `main.spec`

---

## Fase B — Rede de segurança antes de mexer no núcleo

### B-05 · Suíte de testes do núcleo · **M**

Não existe teste automatizado. `teste/` são cinco scripts manuais que exigem webcam e OBS
ligados. Isso destoa do rigor do resto do projeto.

A lógica mais delicada é pura e trivialmente testável, sem I/O:

- `GestureDetector.detectar()` — 21 tuplas entram, string sai
- `GestureStabilityMonitor` — sequência de landmarks entra, bool sai
- `GestureEngine._get_stable_gesture()` — janela de votação
- `_classificar_erro()` — exceção → mensagem
- Migração de modo legado (`test→teste`, `obs→automatico`)

Pré-requisito real do B-06: sem rede, mexer no detector é apostar.

**Sugestão:** `pytest` + fixtures de landmarks gravados de gestos reais (capturar uma vez,
salvar como JSON, virar golden files).

### B-04 · Limpezas pequenas · **P**

Podem ir juntas num commit:

- `core/gesture_detector.py` importa `GESTURE_ALIASES` e **nunca usa** — sobrou da
  consolidação da fase 1.
- Migração de modo legado duplicada em `ui/mixins/config_mixin.py` e
  `engine/gesture_engine.py::_setup`, com os mesmos dois dicts escritos duas vezes.
- `config.json` ainda carrega `virtual_cam_mode`, que a decisão D-13 da fase 15 mandou
  remover.
- `_hand_states` indexado direto por `self._hand_states[hand_id]` — `KeyError` se o
  handedness vier fora de `{"Left","Right"}`.
- `_is_movement_decreasing()` retorna `velocity_trend <= motion_threshold * 0.5`, ou seja
  aceita movimento que **aumentou** até 2px. Não é bug, mas o nome promete mais do que
  entrega e o gate é redundante com `stable_frame_count`. Renomear ou endurecer.

---

## Fase C — Robustez da detecção

### B-06 · Detector não é invariante a rotação · **G**

Duas fragilidades estruturais em `GestureDetector`:

- **`_finger_extended` mede distância até o pulso.** Funciona de frente e ereto. Inclinando
  ou rotacionando a mão, a distância pulso→ponta deixa de discriminar dedo estendido de
  dobrado. O robusto compara a ponta com a articulação PIP ao longo do eixo do dedo.
- **`thumb_up`/`thumb_down` comparam coordenada Y crua** — rotação-dependente por definição.
  Joinha com a mão deitada fica ambíguo, e `FIST` (que exige nem up nem down) pode capturar
  o caso.

Além disso vários gestos diferem por **um único booleano**: `Arminha` vs `POINT` só pelo
`thumb_open`; `V` vs `Escoteiro` só pela distância entre as pontas. A cascata de `if` não
tem margem de confiança nem histerese — a janela de votação (5 de 7) suaviza, mas não
resolve confusão sistemática entre vizinhos.

Num live um falso positivo é caro.

**Medir antes de refatorar:** modo diagnóstico que loga as classificações e revela quais
pares realmente se confundem. Refatorar no escuro aqui é caro e arriscado.

**Depende de:** B-05.

---

## Fase D — Feature

### B-07 · Gestos combinados (duas mãos como unidade) · **G**

Único item genuinamente aberto do planning antigo. O schema já existe (`combined_bindings`
no `config.json`), mas **não há código nenhum** consumindo — só o campo vazio.

A fase 9 entregou detecção independente por mão (D-04: cada mão dispara sua própria binding
com o mesmo pool). Combinados são o passo seguinte: o par esquerda+direita tratado como uma
unidade, com bindings próprias.

Decidir: como o par interage com o cooldown compartilhado (D-05) e com o dispatch
independente (D-04)? Um combinado deve suprimir os dois gestos individuais?

**Arquivos:** `engine/gesture_engine.py`, `ui/tabs/gestos_tab.py`, `config.json`
