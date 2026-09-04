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

### B-11 · Detectar capacidades da câmera e filtrar a UI · **M**

Hoje o app descobre o que a câmera não suporta **falhando** — o D-32 transformou isso num
fallback com aviso, mas a UI segue oferecendo modos inexistentes. A aba Geral mostra
30 e 60 fps para qualquer câmera; a C920 não faz 60 em resolução nenhuma.

`pygrabber` (já é dependência, usado no dropdown de câmeras) enumera os formatos
**instantaneamente, sem abrir o dispositivo pelo FFmpeg**:

```
FilterGraph().get_input_device().get_formats()  ->  35 formatos, 17 deles MJPEG
```

Na C920 todos os 17 MJPEG têm teto de 30 fps. O probe teria pego o bug antes da primeira
falha.

**Por que não fazer por força bruta:** tentar abrir cada combinação custa ~3,5s (1,3s
abrindo + 2,2s no `close`, medidos). Seis combinações = 20s de tela parada no primeiro
boot. O `pygrabber` elimina esse custo.

**Armadilha:** os campos vêm com nome invertido — `min_framerate=30, max_framerate=5`
significa range de 5 a 30. Confiar no rótulo inverte a lógica e filtra ao contrário. Isso
merece um teste que trave a interpretação, não só um comentário.

**Cache velho é pior que cache nenhum:** precisa ser chaveado por nome de dispositivo e
refeito quando o dispositivo muda. Trocar de webcam com cache velho passaria a esconder
modos que funcionam, com a confiança de quem "já analisou".

**O fallback do D-32 continua existindo** — deixa de ser o mecanismo principal e vira a
rede de segurança, que é o papel certo dele.

**Onde mora:** `ui/onboarding.py` já roda no primeiro boot. É ali, não num fluxo novo.

### B-12 · Recomendar preset de câmera · **M** · depende de B-11

Filtrar o que não existe é objetivo. **Recomendar** exige definir "melhor", e isso não é
propriedade da câmera sozinha — é câmera × modo de operação:

- **teste / manual (sem VCam):** resolução acima de 720p é desperdício puro. O
  `HandTracker` reduz tudo para `PROCESS_W=640` antes da inferência, então 1080p custa CPU
  e não melhora detecção em nada.
- **automático:** a resolução **é** o que o público vê no OBS. Aí 1080p importa.

O óbvio ("pega a maior resolução suportada") estaria errado em dois dos três modos.
Decidir isso é o trabalho principal do item — o código é a parte fácil.

### B-13 · UI não reflete o FPS quando o fallback dispara · **P**

Pendência registrada no D-32. Quando a câmera cai de 60 para 30, o usuário recebe o aviso
no status, mas o botão de FPS na aba Geral continua marcando 60. A interface passa a
discordar da realidade até ele trocar na mão.

É a fatia barata do B-11: não precisa de probe nenhum, só propagar o `camera.aviso` /
`camera.fps` efetivo de volta para a UI depois de um start bem-sucedido.
