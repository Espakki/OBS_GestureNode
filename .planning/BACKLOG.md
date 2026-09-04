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

---

## Fase E — Achados da validação do build (B-03)

### B-08 · `config.json` vai parar dentro de `_internal/` no app empacotado · **M**

`main.py` resolve `CONFIG_PATH = Path(__file__).parent / "config.json"`. Congelado,
`__file__` aponta para o `_MEIPASS`, então o config é lido e escrito em
`dist\main\_internal\config.json` — dentro das entranhas do bundle, não ao lado do `.exe`.

Funciona numa pasta de usuário, que é gravável. Mas instalado em `C:\Program Files\`, o
save falha — e falha **em silêncio**: `_do_save_config` captura `OSError` e apenas loga
(`config_mixin.py`). O usuário ajusta os gestos, fecha o app e perde tudo sem nenhum aviso.

Contraria o espírito do D-22, que existe justamente para o config nunca ser corrompido ou
perdido. Corrigido lá o caso de `C:\Windows\system32`; este é a versão empacotada do mesmo
problema.

**Duas coisas a decidir:** onde o config deve morar num app instalado (ao lado do `.exe`?
`%APPDATA%`?) e se um save que falha deve avisar o usuário em vez de só logar.

**Arquivos:** `main.py`, `ui/mixins/config_mixin.py`

### B-09 · `util/hotkey_listener.py` é código morto · **P**

Nenhum arquivo do projeto o importa — confirmado por varredura. Corretamente ausente do
bundle. O D-10 da fase 1 dizia que ele "será integrado na aba de gestos numa fase
posterior"; a captura de atalho acabou sendo implementada direto em `ui/tabs/gestos_tab.py`.

Decidir: apagar, ou manter e integrar? Se ninguém sente falta, apagar é mais honesto que
deixar 230 linhas parecendo que fazem parte do sistema.

### B-10 · `dist/main` tem 774 MB · **M**

`collect_all('mediapipe')` arrasta `jax`, `jaxlib`, `scipy`, `matplotlib` e `PIL` junto —
nenhum deles usado pelo projeto. Dá para cortar com `excludes` no spec.

Mexida arriscada: cortar demais quebra o carregamento dos `.tflite` de um jeito que só
aparece em runtime. Só encarar com o build sendo testado a cada passo, e depois que o
`.exe` estiver validado funcionando (senão não dá para saber se a quebra veio do corte).
