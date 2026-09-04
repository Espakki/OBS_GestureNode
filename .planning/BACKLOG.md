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

### B-03 · Validar o `main.spec` contra as deps atuais · **M**

O spec é de maio, quando não havia PyAV nem pygrabber. Tem `hiddenimports=[]` e só
`collect_all('mediapipe')`. PyAV traz DLLs do FFmpeg; `pygrabber` usa `comtypes`, que gera
módulos em runtime — os dois são historicamente problemáticos no PyInstaller.

Não dá pra afirmar que quebra sem rodar. Validar cedo, não na véspera de distribuir.

**Arquivos:** `main.spec`

---

## Fase B — Rede de segurança antes de mexer no núcleo

_Fechada: B-05 em `627d997`, B-04 em `70fe7cf`._

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

**Depende de:** B-05 (fechado em `627d997` — a rede existe).

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
