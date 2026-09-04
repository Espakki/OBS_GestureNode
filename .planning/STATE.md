# Onde o projeto está

> **Este é o único arquivo que diz status.** Se outro arquivo parecer contradizer este,
> este vence — e o outro está com bug. Atualize-o ao fim de toda sessão de trabalho.

**Última atualização:** 2026-09-04
**Branch:** `main` · **Último commit:** `f8e3ca3`

---

## Resumo em 30 segundos

App desktop Windows que controla o OBS por gestos de mão via webcam. Funcional e já
empacotável. O núcleo (detecção, engine, OBS, UI com tema escuro, 2 mãos, 3 modos de
operação) está entregue, com 141 testes automatizados cobrindo detector, estabilidade,
despacho por mão e caminhos de config.

**Estado real:** validado rodando do código-fonte com câmera, OBS e mãos reais em
2026-09-04 — conexão OBS, VCam em resolução nativa, esqueleto na saída, joinha, duas mãos
e o ciclo parar/iniciar. **O `.exe` empacotado nunca foi aberto por ninguém.**

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

---

## Próximo

Em ordem. Detalhes e justificativa em [BACKLOG.md](BACKLOG.md).

1. **Abrir o `.exe`** (itens 6–8 abaixo). É o único bloco de validação que resta, e
   destrava o B-10.
2. **B-15 — Config do OBS não aplica na engine viva.** Precisa de decisão: reconectar
   sozinho ou avisar que o campo exige restart?
3. **B-11 — Detectar capacidades da câmera.**

A pendência do B-01 (converter `av` para pin exato) está fechada em `9e044dd`. Ver D-25.

---

## Bloqueios

- **Nenhum bloqueio de ambiente.** Python 3.10.11 instalado em
  `C:\Users\wini\AppData\Local\Programs\Python\Python310`, `.venv/` recriado do zero e
  validado. O `venv/` antigo, que apontava para `C:\Users\Computer\...` (outro PC), foi
  apagado — junto com ele se perderam os pins que funcionavam na máquina anterior.
- **Rodando do código-fonte está validado.** O que segue sem verificação é só o `.exe`
  empacotado — e é ele que bloqueia o B-10, porque sem um baseline de "funciona" não dá
  para saber se um corte de dependência quebrou algo ou se já estava quebrado.

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

### Ainda falta: o executável empacotado

1. `dist\main\main.exe` abre sem message box de erro
2. Preview da câmera funciona (valida PyAV/dshow empacotado)
3. Dropdown lista as câmeras (valida comtypes congelado)
4. Copiar `dist\main\` para `C:\Program Files\`, rodar de lá e mexer num slider: deve
   **avisar** que não está salvando, não falhar em silêncio (B-08)

### Números calibrados com mão real (2026-09-04)

- **`TOLERANCIA_POLEGAR_GRAUS = 45`** (D-36) — validado. O valor original de 60° aceitava
  um polegar na diagonal a ~50°, que o usuário não considera joinha.
- **`COMPRIMENTO_MINIMO_POLEGAR = 0.55`** (D-35) — validado no mesmo teste.
- **Espessura do esqueleto** (D-33): conferir no OBS se ficou boa em 1080p.
