# Onde o projeto está

> **Este é o único arquivo que diz status.** Se outro arquivo parecer contradizer este,
> este vence — e o outro está com bug. Atualize-o ao fim de toda sessão de trabalho.

**Última atualização:** 2026-09-04
**Branch:** `main` · **Último commit:** `8ffbc2b`

---

## Resumo em 30 segundos

App desktop Windows que controla o OBS por gestos de mão via webcam. Funcional e já
empacotável. O núcleo (detecção, engine, OBS, UI com tema escuro, 2 mãos, 3 modos de
operação) está entregue, com 131 testes automatizados cobrindo detector, estabilidade,
despacho por mão e caminhos de config.

**Estado real:** o app já foi executado pelo dono e o ciclo parar/reiniciar da câmera foi
reproduzido e corrigido contra a C920 real. O que segue sem verificação de runtime é o
`.exe` empacotado, a câmera virtual no OBS e a conexão OBS — ver a lista no fim.

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

---

## Próximo

Em ordem. Detalhes e justificativa em [BACKLOG.md](BACKLOG.md).

1. **B-10 — Cortar as 774 MB do `dist`.** Em andamento.

A pendência do B-01 (converter `av` para pin exato) está fechada em `9e044dd`. Ver D-25.

---

## Bloqueios

- **Nenhum bloqueio de ambiente.** Python 3.10.11 instalado em
  `C:\Users\wini\AppData\Local\Programs\Python\Python310`, `.venv/` recriado do zero e
  validado. O `venv/` antigo, que apontava para `C:\Users\Computer\...` (outro PC), foi
  apagado — junto com ele se perderam os pins que funcionavam na máquina anterior.
- **Câmera real já foi exercitada** (ciclo parar/iniciar, 3x seguidas, na C920). Seguem sem
  verificação: o `.exe` empacotado, a câmera virtual dentro do OBS e a conexão OBS.

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

## Pendente: validação com o app rodando

Nada abaixo foi exercitado — tudo que veio depois de `9e044dd` foi verificado por teste
automatizado e análise estática, sem câmera, sem OBS e sem abrir o `.exe`.

**Câmera virtual (B-02)**
1. Modo automático + OBS: imagem da VCam nítida em 1080p, não borrada
2. Checkbox "esqueleto na saída do OBS" desligado → esqueleto só no preview; ligado → nos dois

**Polegar (B-06) — o mais importante**
3. Joinha com a mão bem inclinada deve virar "nenhum gesto", **nunca** deslike
4. Joinha e deslike normais ainda disparam confortavelmente
5. Se 60° estiver apertado demais (joinha natural não dispara), ajustar
   `TOLERANCIA_POLEGAR_GRAUS` no topo de `core/gesture_detector.py`

**Executável (B-03)**
6. `dist\main\main.exe` abre sem message box de erro
7. Preview da câmera funciona (valida PyAV/dshow empacotado)
8. Dropdown lista as câmeras (valida comtypes congelado)

**Config (B-08)**
9. Copiar `dist\main\` para `C:\Program Files\`, rodar de lá e mexer num slider:
   deve **avisar** que não está salvando, não falhar em silêncio
10. Rodando da pasta normal, a config persiste entre aberturas

**Duas mãos (D-31)**
11. Com as duas mãos em quadro fazendo gestos diferentes, disparar **só uma** ação
12. A ação disparada deve ser a da mão que começou o gesto primeiro
13. Uma mão só continua funcionando normalmente

**Parar e reiniciar (novo)**
14. Iniciar, parar, iniciar de novo: deve voltar a funcionar sem erro de câmera
15. Ao parar, a UI mostra "Parando..." por ~2,5s antes de liberar o Start — é esperado
16. Trocar entre 1 e 2 mãos com a engine rodando: ela deve parar E religar sozinha
