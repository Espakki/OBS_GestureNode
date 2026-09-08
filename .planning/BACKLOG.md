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

_B-22 fechado em `0ab76f5`, B-23 em `f34fe59`._

### B-26 · Executar o app num Linux de verdade · **M** · precisa de máquina Linux

O código do B-23 está escrito e testado na forma do comando, **nunca no efeito**. Os mapas
de keycode saíram do `input-event-codes.h` e jamais encostaram num kernel. Enquanto isso
não acontecer, o Linux é "escrito, não verificado" — e o projeto já pagou uma vez para
aprender que câmera e injeção de tecla só se provam no hardware. Ver D-46.

**O que verificar, em ordem:**
1. `pip install -r requirements.txt` completa (era o que o `pygrabber` sem marcador quebrava)
2. O app abre e a webcam aparece no preview via `/dev/video0`
3. Um atalho chega ao OBS — testar no X11 **e** no Wayland, que usam injetores diferentes
4. O som toca
5. Câmera virtual: exige o módulo `v4l2loopback` carregado, o que é configuração de máquina

**Achado provável, não bug:** a listagem de câmeras usa `QMediaDevices`, que é portável,
mas o filtro de capacidades depende do `pygrabber` e vai falhar em aberto no Linux — o app
oferece todas as resoluções e descobre o limite falhando. É o comportamento projetado
(D-38), não uma regressão.

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

---

## Fase L — Antes de publicar o binário

### B-27 · Verificar a compatibilidade de licença do `pyvirtualcam` · **P** · pode bloquear o release

Achado ao gerar o catálogo de licenças (D-51). O `pyvirtualcam==0.15.0` se declara com o
classificador **`GNU General Public License v2 (GPLv2)`** — não `GPLv2+` —, e o texto que
ele distribui é o da GPL-2.0.

**Se for GPLv2-only, é incompatível com a GPL-3.0 deste projeto.** As duas licenças não são
compatíveis entre si, e distribuir um binário que combina as duas seria distribuir sem
permissão. Isso não afeta rodar do código-fonte para uso próprio; afeta **publicar o
pacote**.

**Não confirmei.** O classificador do PyPI sugere "only", mas o projeto pode declarar "ou
posterior" em outro lugar. Antes de qualquer release público, conferir na fonte:
<https://github.com/letmaik/pyvirtualcam>.

**Saídas, se confirmar a incompatibilidade:**
- O upstream aceitar relicenciar ou esclarecer que é GPLv2+
- Trocar a biblioteca de câmera virtual
- O projeto passar para GPL-2.0-or-later, o que muda o D-44
- Deixar a câmera virtual como componente separado, fora do binário

Nenhuma é rápida — daí registrar agora, e não na véspera do lançamento.

### B-28 · Comparar versão com o último release e avisar no app · **P** · depende do D-51

O `version.py` existe e o app já sabe a própria versão. Falta consultar
`api.github.com/repos/Espakki/OBS_GestureNode/releases/latest`, comparar, e mostrar um aviso
com link para a página do release.

Decidido em conversa: **não baixa nem instala nada** — só avisa e leva ao GitHub. Sem UAC,
sem instalador disparado por conta própria, sem download pela metade para tratar. E como o
release sai por tag, e não por commit, o peso do download deixa de importar.

Detalhes que valem lembrar: a API do GitHub limita a 60 chamadas por hora por IP sem
autenticação (suficiente para uma checagem por abertura), e ficar offline não pode virar
diálogo de erro.
