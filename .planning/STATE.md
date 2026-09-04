# Onde o projeto está

> **Este é o único arquivo que diz status.** Se outro arquivo parecer contradizer este,
> este vence — e o outro está com bug. Atualize-o ao fim de toda sessão de trabalho.

**Última atualização:** 2026-09-03
**Branch:** `main` · **Último commit:** `2a4e119`

---

## Resumo em 30 segundos

App desktop Windows que controla o OBS por gestos de mão via webcam. Funcional e já
empacotável. O núcleo (detecção, engine, OBS, UI com tema escuro, 2 mãos, 3 modos de
operação) está entregue. O que falta é robustez: ausência de testes automatizados e a
fragilidade do detector a rotação.

**Estado real:** a instalação limpa foi validada nesta máquina — Python 3.10.11, `.venv`
recriado, os 10 imports do projeto passam. O app em si ainda não foi executado aqui:
câmera, VCam e OBS seguem sem verificação de runtime.

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

---

## Próximo

Em ordem. Detalhes e justificativa em [BACKLOG.md](BACKLOG.md).

1. **B-08 — `config.json` dentro do `_internal`.** Perda silenciosa de config em instalação protegida.
2. **B-07 — Gestos combinados.** Última feature do planning antigo ainda aberta.
3. **B-09 — Apagar ou integrar o `hotkey_listener` morto.**

A pendência do B-01 (converter `av` para pin exato) está fechada em `9e044dd`. Ver D-25.

---

## Bloqueios

- **Nenhum bloqueio de ambiente.** Python 3.10.11 instalado em
  `C:\Users\wini\AppData\Local\Programs\Python\Python310`, `.venv/` recriado do zero e
  validado. O `venv/` antigo, que apontava para `C:\Users\Computer\...` (outro PC), foi
  apagado — junto com ele se perderam os pins que funcionavam na máquina anterior.
- **Instalar não é funcionar.** Nada de runtime foi exercitado: câmera, VCam e conexão OBS
  nunca subiram aqui. B-02 e B-03 continuam sem verificação de fato.

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
