# Backlog

Itens abertos, em ordem de prioridade. Sem checkbox de progresso por decisão de projeto:
status vive só no [STATE.md](STATE.md). Quando um item fecha, ele sai daqui e vira uma
linha com SHA lá.

Tamanho: **P** = uma sessão curta · **M** = uma sessão · **G** = várias sessões, merece
plano em `active/`.

---

## Fase A — Fazer o app subir em ambiente limpo

_Fechada: B-01 em `9e044dd`, B-02 em `7a383e2`, B-03 em `2a4e119`._

Objetivo: `git clone` + `pip install -r requirements.txt` + `python main.py` funciona numa
máquina virgem. Hoje não funciona.

---

## Fase B — Rede de segurança antes de mexer no núcleo

_Fechada: B-05 em `627d997`, B-04 em `70fe7cf`._

---

## Fase C — Robustez da detecção

_Fechada: B-06 em `6080496`. Falta validar com câmera real a tolerância de 60° (D-28)._

---

## Fase D — Feature

_Fechada: B-07 em `9565642`._

---

## Fase E — Achados da validação do build (B-03)

_B-08 fechado em `ebf2fc1`, B-09 em `2074859`._

### B-10 · `dist/main` tem 774 MB · **M**

`collect_all('mediapipe')` arrasta `jax`, `jaxlib`, `scipy`, `matplotlib` e `PIL` junto —
nenhum deles usado pelo projeto. Dá para cortar com `excludes` no spec.

Mexida arriscada: cortar demais quebra o carregamento dos `.tflite` de um jeito que só
aparece em runtime. Só encarar com o build sendo testado a cada passo, e depois que o
`.exe` estiver validado funcionando (senão não dá para saber se a quebra veio do corte).

---

## Fase F — Câmera: saber antes de falhar

_Fechada: B-13 em `c7715b0`, B-11 em `f7a92a9`, B-12 em `035a4c5`._


---

## Fase H — Pontas soltas

_B-20 fechado em `e28e0bf`._

### B-21 · Trocar o framework da UI · **G** · ideia, não decisão

Levantado pelo dono em 2026-09-04, sem compromisso: vontade de reavaliar o PySide6 para a
interface. Registrado só para não se perder.

**Antes de encarar, vale saber o que se perde:** o PySide6 hoje carrega a `QThread` da
engine, os `Signal` que ligam engine e UI (a fronteira que o CLAUDE.md trata como
invariante), o `QMediaDevices` da listagem de câmeras e o tema em QSS (D-19). Trocar a UI
significa reescrever essa ponte inteira, não só as telas.

**Não é item de backlog no sentido usual** — é uma decisão de arquitetura que precisa de
motivo concreto (o que exatamente o PySide6 está impedindo?) antes de virar plano.

---

## Fase I — Port para Linux

### B-22 · Abstrair a camada de plataforma · **G** · pré-requisito do B-23

O app é Windows-only por construção, não por acidente. O planning antigo já tinha previsto
isto como *Phase 7 — Platform Abstraction*, absorvida na v1.2 e **nunca executada**.

**Cinco pontos de acoplamento**, levantados por varredura:

| Ponto | Onde | Windows | Linux |
|---|---|---|---|
| Áudio | `action_manager._tocar_som` | `winsound` | `simpleaudio`, `paplay`, ou `aplay` |
| Hotkeys | `action_manager`, ~130 linhas | `ctypes.WinDLL("user32")` + `SendInput` | `ydotool`/`evdev` no Wayland, `xdotool`/`Xlib` no X11 |
| Captura | `camera._tentar_abrir` | `format='dshow'` | `format='v4l2'`, device em `/dev/videoN` |
| Capacidades | `capacidades_camera` | `pygrabber` (**não existe em Linux**) | `v4l2-ctl --list-formats-ext` ou ioctl direto |
| Config | `util/caminhos` | `%APPDATA%` | `$XDG_CONFIG_HOME` / `~/.config` |

**41% de `action_manager.py` é código Windows** (~152 de 367 linhas), quase tudo no envio de
teclas. É o ponto mais caro do port, e o mais chato de testar sem a máquina alvo.

**As dependências quase todas já cruzam:** PySide6, opencv, mediapipe, av, obsws-python e
websocket-client rodam em Linux. `pyvirtualcam` também, mas exige o módulo de kernel
`v4l2loopback` instalado — ou seja, o modo automático depende de setup fora do app.
`keyboard` funciona, mas **exige root** em Linux. **`pygrabber` não tem substituto direto**
e precisa ser reescrito.

**O núcleo já é portátil.** Detector, monitor de estabilidade, aliases, modos, despacho por
mão e cliente OBS não têm nada de plataforma — e são justamente os que têm os 174 testes.
A fronteira já está quase desenhada, só não está explícita.

**Escopo desta fase:** criar `platform/` com uma interface e a implementação Windows,
movendo o código existente para lá **sem mudar comportamento**. Nada de Linux ainda. Isso
deixa o port como preenchimento de uma interface conhecida, em vez de arqueologia.

### B-23 · Implementação Linux · **G** · depende de B-22

Preencher a interface do B-22. **Não dá para fazer daqui**: exige máquina ou VM Linux para
qualquer verificação — e a lição desta semana é que câmera e entrada de teclado só se
provam no hardware real.

**Decidir antes:** X11, Wayland, ou os dois? A diferença não é detalhe — no Wayland, injetar
teclas exige `ydotool` com daemon e permissão, enquanto no X11 o `xdotool` resolve direto.
Suportar os dois quase dobra o trabalho da parte mais cara.
