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

---

## Fase G — Achados da validação manual (2026-09-04)

Vieram da primeira validação com câmera, OBS e mãos de verdade. Passaram sem ressalva:
conexão OBS em automático, resolução nativa da VCam, esqueleto na saída, joinha sem
confusão, duas mãos com uma ação só, e o ciclo parar/iniciar/reiniciar.

### B-14 · Esqueleto fica fino demais em resolução alta · **P**

O `draw_landmarks` do MediaPipe usa `DrawingSpec(thickness=2)` — **espessura fixa em
pixels**, não proporcional ao frame:

| Frame | Linha de 2px ocupa |
|---|---|
| 640px | 0,31% da largura |
| 1920px | 0,10% da largura |

Três vezes mais fina em 1080p. Foi percebido como "upscale da fonte no OBS", mas **não é
upscale** — o frame nativo está correto (B-02 fez o que devia). É só o esqueleto que não
acompanhou a escala.

**Correção:** derivar `thickness` e `circle_radius` da largura do frame.

### B-15 · Config do OBS não aplica na engine em execução · **M**

`on_obs_changed` grava host/porta/senha no config, mas **nunca reaplica na engine viva** —
a conexão foi feita no start com os valores antigos. Gestos, esqueleto e hold/cooldown
aplicam ao vivo (`on_dynamic_setting_changed`); OBS não.

Para o usuário parece que "não salvou", quando na verdade salvou e não surtiu efeito.

**Decidir:** reconectar sozinho ao mudar host/porta, ou avisar na UI que aquele campo
precisa de restart? Reconectar a cada tecla digitada no campo de host seria pior — exige
debounce ou um botão explícito.

**Relacionado:** `set_config_enabled` desabilita só câmera, resolução e FPS enquanto roda.
O resto fica editável, o que é bom — mas então tudo que fica editável deveria aplicar.

### B-16 · Pipeline de frame com ~5,8 ms de gordura · **M**

Medido em 1080p, modo automático com esqueleto na VCam (o caminho do usuário):

| Etapa | Custo |
|---|---|
| Inferência MediaPipe | 20,7 ms (piso, não dá pra cortar) |
| `resize` 1080p→640 `INTER_AREA` | 2,06 ms |
| `copy()` do frame nativo para a VCam | 2,20 ms |
| `desenhar_esqueleto` em 1080p | 2,15 ms |
| `cvtColor` BGR→RGB em 1080p | 2,00 ms |

~27 ms de CPU contra um orçamento de 33,3 ms a 30 fps: **80% de utilização**, o que explica
a latência percebida. Três ganhos identificados:

1. **A cópia é redundante.** `ler_frame()` já devolve `self._ultimo_frame.copy()`, e
   `processar()` não muta o frame recebido — ele cria o reduzido separado. O
   `frame_nativo.copy()` que eu adicionei no B-02 é uma segunda cópia desnecessária.
   **−2,2 ms, sem contrapartida.**
2. **`pyvirtualcam` aceita `PixelFormat.BGR`**, dispensando o `cvtColor`. **−2,0 ms.**
3. **`INTER_AREA` → `INTER_LINEAR`** no resize: 2,06 → 0,42 ms. **−1,6 ms, mas com
   contrapartida:** `INTER_AREA` tem qualidade melhor em redução e o alvo é a entrada da
   inferência. Precisa medir se a detecção piora antes de trocar.

**Nota:** `max_num_hands` **não** é alavanca — 1 mão custa 21,8 ms e 2 mãos custam 20,7 ms.
A tolerância de duas mãos do D-31 é gratuita.

### B-17 · UI trava e pisca ao parar a engine · **M**

`GestureEngine.stop()` chama `self.wait(8000)` **a partir da thread da UI**, que é o que
congela a janela por ~2,5 s (o `container.close()` do DirectShow, medido no D-32).

Introduzido por mim ao corrigir o bug de parar/reiniciar: o `wait` garante que a câmera foi
liberada antes de retornar, mas paga com a UI travada.

**O padrão Qt correto** é não bloquear: `stop()` só sinaliza, e o sinal `finished` dirige a
UI. A infraestrutura já existe — `stop_engine` já mostra "Parando..." e já espera o
`finished` para reabilitar o Start. O `wait` virou redundante com essa mudança.

**Cuidado:** o `restart_engine` depende de a parada ter terminado antes do novo start.
Remover o `wait` sem encadear pelo `finished` traria o bug do `[Errno 5]` de volta.

### B-18 · Trocar 1↔2 mãos reinicia sem avisar · **P**

O restart automático funciona, mas acontece sem aviso: a câmera apaga e volta sozinha, o
que assusta. Pedir confirmação antes ("isso vai reiniciar a captura, continuar?") e só
então reiniciar.

### B-19 · Joinha de lado ainda é aceito · **P** · polimento do D-28

Com o polegar apontando para o lado/para trás (não inclinado, mas rotacionado no eixo da
profundidade), o gesto ainda registra como joinha. Tecnicamente cumpre todos os critérios:
os quatro dedos dobrados e o polegar dentro da tolerância angular.

A causa é que `_angulo_do_polegar` mede só X/Y. Um polegar apontando para a câmera ou para
longe dela **projeta um vetor curto**, e o ângulo desse vetor curto ainda pode cair dentro
dos 60°.

**Ideia:** exigir um comprimento mínimo do vetor polegar, proporcional ao `palm_size`. Um
polegar muito encurtado na projeção está apontando na profundidade, e aí a orientação
X/Y não significa nada.

**Prioridade baixa** por decisão do dono: não atrapalha o uso, é polimento.
