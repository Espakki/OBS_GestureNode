# Onde o projeto está

> **Este é o único arquivo que diz status.** Se outro arquivo parecer contradizer este,
> este vence — e o outro está com bug. Atualize-o ao fim de toda sessão de trabalho.

**Última atualização:** 2026-09-09
**Branch:** `feat/casca-remodelada` · **Último commit de código:** `af54479`

> Este campo aponta o último commit que mexeu em **código** — commits só de documentação
> não o movem. Como referência ao próprio commit que o edita, ele já se corrompeu duas vezes.

---

## Resumo em 30 segundos

App desktop Windows que controla o OBS por gestos de mão via webcam. Funcional e já
empacotável. O núcleo (detecção, engine, OBS, UI com tema escuro, 2 mãos, 3 modos de
operação) está entregue, com 251 testes automatizados cobrindo detector, estabilidade,
despacho por mão, caminhos de config, tradução de atalho e a casca nova.

**A interface é QML desde 2026-09-08** (D-49), e desde 2026-09-09 há uma **terceira
opção**: a casca remodelada, com rail vertical no lugar das abas (D-52). Três caminhos
convivem — sem variável abre a de abas, `GESTURENODE_UI=novo` abre a remodelada,
`GESTURENODE_UI=widgets` abre a antiga de Qt Widgets.

**Estado real:** validado rodando do código-fonte com câmera, OBS e mãos reais em
2026-09-04 — conexão OBS, VCam em resolução nativa, esqueleto na saída, joinha, duas mãos
e o ciclo parar/iniciar. O `.exe` empacotado foi aberto e usado em 2026-09-08, e rodou
bem — o único achado, a faixa de limite da câmera, está corrigido em `13ee25c`.

---

## Entregue

Cada linha aponta pro commit. Sem SHA, não está entregue.

| Área | Commit | O que fechou |
|---|---|---|
| MVP v1.0 | `a970f0b` | Engine, gestos, UI, hotkeys, ícones |
| Foundation | `310c059` | Deps pinadas, `gesture_aliases` unificado, RLock nas bindings, save atômico do config |
| Engine & OBS | `590f993` | Engine não-bloqueante, FPS cap, conexão OBS assíncrona |
| Câmera | `76607d8` | Aspect ratio, frame staleness, buffer DirectShow, migração pra PyAV |
| Modos & 2 mãos | `ba1916d` | Modos teste/manual/automático, VCam, `HandTracker` multi-mão com handedness |
| UI | `b6a55b8` | `MainWindow` extraída em mixins por domínio |
| Polish | `e61397e` | Configurações Avançadas, tema Streamer Dark, supressão de preview |
| Repo | `c9d2271` | Build PyInstaller versionado, `config.json` destrackeado, README |
| Planning | `a7b0dd6` | Modelo GSD substituído por 4 arquivos; `CLAUDE.md` na raiz |
| Deps | `28dcb61` | `av` e `websocket-client` declarados — B-01 fechado |
| Deps | `9e044dd` | `av` pinado em 14.2.0, `opencv-contrib` travado; instalação limpa validada |
| Câmera | `7a383e2` | VCam com resolução nativa e toggle próprio de esqueleto — B-02 fechado |
| Testes | `627d997` | 65 testes do núcleo com landmarks sintéticos — B-05 fechado |
| Limpeza | `70fe7cf` | `core/modos.py` unifica migração de modo divergente — B-04 fechado |
| Detector | `6080496` | Joinha/deslike por ângulo com zona morta — B-06 fechado |
| Build | `2a4e119` | Wrappers comtypes congelados, UPX desligado — B-03 fechado |
| Config | `ebf2fc1` | Config em `%APPDATA%` no app empacotado, com aviso de falha — B-08 fechado |
| Limpeza | `2074859` | `hotkey_listener` morto removido — B-09 fechado |
| Feature | `9565642` | Gestos combinados — **revertido** em `a7a1088`, ver D-31 |
| Câmera | `9a0aad9` | Corrige falha ao parar e reiniciar a captura |
| Engine | `a7a1088` | Duas mãos rastreadas, uma ação só: a primeira vence (D-31) |
| Câmera | `9ef7217` | `[Errno 5]` ambíguo: retry curto + fallback de FPS (D-32) |
| Polimento | `f41d5c2` | Traço proporcional, VCam em BGR, confirmação ao reiniciar — B-14/16/18 |
| UI | `c7715b0` | Parada assíncrona e FPS acompanhando o fallback — B-17/13 |
| Detector | `8ffbc2b` | Polegar em profundidade não vira joinha — B-19 |
| Detector | `f8e3ca3` | Tolerância do polegar 60°→45°, calibrada com foto real (D-36) |
| OBS | `512beb4` | Cena inexistente não derruba a conexão — B-15 |
| Câmera | `f7a92a9` | UI filtra modos que a câmera não oferece — B-11 |
| Câmera | `035a4c5` | Faixa de limitação na tela e preset por modo — B-12 |
| UI | `5aea31f` | Aba Geral fala por forma, não por parágrafo (D-40) |
| Docs | `c0a7a4a` | LICENSE (MIT) e README reescrito |
| Release prep | `44c5ef6` | LICENSE GPL-3.0, README, CHANGELOG, build 774→480 MB |
| Plataforma | `0ab76f5` | `plataforma/` isola o SO; testes de atalho migrados — B-22 |
| Plataforma | `f34fe59` | `_linux.py`: xdotool/wtype/ydotool + som — B-23 (D-46) |
| Arquitetura | `66da7f0` | Estado sai da UI: `core/estado_app.py` e amigos (D-47, D-48) |
| UI | `afac56b` | Aba Geral em QML, atrás de um contrato (D-49) |
| UI | `2c8ffac` | Barra de rolagem própria; aba OBS em QML |
| Atalhos | `e371776` | Tradução de tecla extraída; teste do AltGr corrigido (D-50) |
| UI | `89c7386` | Aba Gestos em QML — as três abas migradas |
| Build | `247ef41` | `.qml` no pacote; queda para Widgets visível e sem vazamento |
| Release | `4b9a9cb` | `version.py`, aba Sobre com licenças, D-47 a D-51 |
| UI | `13ee25c` | Faixa de limite da câmera perde o tom de alerta — B-25 (D-45) |
| UI | `af54479` | Casca remodelada em `GESTURENODE_UI=novo`: rail, botão único, gaveta de diagnóstico, onboarding em QML (D-52) |
| UI | `PENDENTE2` | Tela `Ao vivo` para calibrar; teto de largura removido; preview lateral 372→440 (D-53) |

---

## Próximo

Em ordem. Detalhes e justificativa em [BACKLOG.md](BACKLOG.md).

1. **Construir o `.exe` com a interface nova.** É a validação que falta: os `.qml` agora
   entram no pacote (`247ef41`), mas isso nunca foi exercitado num build de verdade — e a
   casca nova acrescentou `ui/qml/novo/`, que depende de o `datas` copiar a árvore toda.
2. **B-27 — Licença do `pyvirtualcam`.** Pode travar o release público. Verificar antes de
   investir em qualquer outra coisa de publicação.
3. **B-26 — Executar o app num Linux de verdade.** Precisa de máquina ou VM Linux.
4. **B-28 — Aviso de atualização** comparando com o último release do GitHub.

---

## Bloqueios

- **Nenhum bloqueio de ambiente.** Python 3.10.11 instalado em
  `C:\Users\wini\AppData\Local\Programs\Python\Python310`, `.venv/` recriado do zero e
  validado. O `venv/` antigo, que apontava para `C:\Users\Computer\...` (outro PC), foi
  apagado — junto com ele se perderam os pins que funcionavam na máquina anterior.
- **Nada bloqueando no Windows para rodar do código-fonte.** Validado com a interface QML.
- **O `.exe` atual (de 2026-09-04) é anterior à migração de UI.** Um build novo é a próxima
  verificação, e nele mora o risco que o `247ef41` endereçou: sem os `.qml` no pacote, o app
  cairia para a interface antiga. Agora isso aparece no log da janela em vez de acontecer em
  silêncio.
- **O Linux está escrito e não verificado.** `plataforma/_linux.py` existe, escolhe o
  injetor pela sessão gráfica e passa em 26 testes — que cobrem a **forma do comando**, não
  o efeito dele. Nunca foi executado em Linux. Não conte como entregue ao usuário até o
  B-26. Ver D-46.

---

## Como retomar depois de um tempo parado

1. `git pull` — **antes de qualquer análise.** Já aconteceu de o checkout local estar 4
   meses atrás do remoto e a leitura do código sair toda errada.
2. Leia este arquivo, depois [DECISIONS.md](DECISIONS.md) antes de julgar qualquer escolha
   de design como estranha. Muita coisa que parece inconsistente é decisão registrada.
3. Confira [PITFALLS.md](PITFALLS.md) antes de mexer em câmera, MediaPipe ou VCam.
4. `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`

## Como fechar uma sessão

Atualize a tabela **Entregue** com o SHA, tire o item do **Próximo**, e registre em
[DECISIONS.md](DECISIONS.md) qualquer escolha que um leitor futuro possa achar arbitrária.

---

## Validação

**Feito em 2026-09-04, rodando do código-fonte** — conexão OBS em automático; VCam nítida
em resolução nativa; esqueleto na saída do OBS; joinha sem falso positivo; duas mãos com
uma ação só; ciclo parar/iniciar/reiniciar; e a parada sem travar a UI.

Achados viraram B-14 a B-19, todos fechados. A queixa de resolução era da cena do OBS, não
do app.

### Executável empacotado — feito em 2026-09-08

`dist\main\main.exe` (480 MB, o build já enxugado do B-10) abriu e rodou bem em uso
normal. Isso cobre o que o corte de dependências podia ter quebrado: a message box de erro
no boot, o preview da câmera (PyAV/dshow empacotado) e a listagem de câmeras (comtypes
congelado).

**Persistência do config confirmada:** alterações feitas nos sliders sobrevivem a fechar e
reabrir o app. É o resultado esperado, e não por sorte — empacotado, o config vai para
`%APPDATA%` (D-29), que é gravável independentemente de onde o `.exe` esteja. O aviso do
B-08 é o caminho de **falha**: ele só aparece se o save não der certo, então não vê-lo é a
aprovação, não a ausência do teste.

Achado único: a faixa de limite da câmera lia como alerta urgente sem ser. Corrigido em
`13ee25c`, ver D-45.

### Números calibrados com mão real (2026-09-04)

- **`TOLERANCIA_POLEGAR_GRAUS = 45`** (D-36) — validado. O valor original de 60° aceitava
  um polegar na diagonal a ~50°, que o usuário não considera joinha.
- **`COMPRIMENTO_MINIMO_POLEGAR = 0.55`** (D-35) — validado no mesmo teste.
- **Espessura do esqueleto** (D-33): conferir no OBS se ficou boa em 1080p.
