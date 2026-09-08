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

_Fechada: B-06 em `6080496`. Tolerância validada com mão real e ajustada de 60° para
45° (D-36)._

---

## Fase D — Feature

_Fechada: B-07 em `9565642`._

---

## Fase E — Achados da validação do build (B-03)

_Fechada: B-08 em `ebf2fc1`, B-09 em `2074859`, B-10 em `44c5ef6`._

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

_B-22 fechado em `0ab76f5`._

### B-23 · Implementação Linux · **G** · depende de B-22

Preencher a interface do B-22. **Não dá para fazer daqui**: exige máquina ou VM Linux para
qualquer verificação — e a lição desta semana é que câmera e entrada de teclado só se
provam no hardware real.

**Decidir antes:** X11, Wayland, ou os dois? A diferença não é detalhe — no Wayland, injetar
teclas exige `ydotool` com daemon e permissão, enquanto no X11 o `xdotool` resolve direto.
Suportar os dois quase dobra o trabalho da parte mais cara.

---

## Fase J — Obrigações de licença na distribuição

### B-24 · Cumprir as obrigações de LGPL e GPL no pacote do release · **P**

O app é GPL-3.0 (D-44), mas o **pacote distribuído** tem obrigações que o arquivo `LICENSE`
sozinho não cumpre.

**PySide6 é LGPL-3.0.** Distribuir o bundle do PyInstaller com o Qt embutido exige, entre
outras coisas, incluir o texto da LGPL e não impedir que o usuário substitua a biblioteca
Qt por outra versão. Bundle congelado torna a substituição difícil — o caminho usual é
oferecer, junto ao release, o código-fonte e as instruções de rebuild, que este projeto já
tem no README.

**A GPL exige o código-fonte correspondente.** Como o repositório é público e o release sai
com tag, isso já está satisfeito na prática — mas o texto do release deve **apontar
explicitamente** para o código da tag correspondente, não deixar implícito.

**A fazer no pacote do release:**
- Incluir `LICENSE` (GPL-3.0) na raiz do zip
- Incluir um `LICENSES-TERCEIROS.txt` com os textos de LGPL-3.0, GPL-2.0, Apache-2.0,
  BSD-3-Clause e MIT, e quais pacotes usam cada uma
- Na descrição do release, linkar a tag do código-fonte

Não é urgente para uso pessoal; passa a importar quando o binário for distribuído
publicamente.
