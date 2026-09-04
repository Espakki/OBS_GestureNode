# Onde o projeto está

> **Este é o único arquivo que diz status.** Se outro arquivo parecer contradizer este,
> este vence — e o outro está com bug. Atualize-o ao fim de toda sessão de trabalho.

**Última atualização:** 2026-09-03
**Branch:** `main` · **Último commit:** `c9d2271`

---

## Resumo em 30 segundos

App desktop Windows que controla o OBS por gestos de mão via webcam. Funcional e já
empacotável. O núcleo (detecção, engine, OBS, UI com tema escuro, 2 mãos, 3 modos de
operação) está entregue. O que falta é robustez: uma dependência não declarada que
quebra instalação limpa, qualidade da câmera virtual, e ausência de testes.

**Estado real:** roda, mas nunca foi validado em ambiente limpo.

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

---

## Próximo

Em ordem. Detalhes e justificativa em [BACKLOG.md](BACKLOG.md).

1. **B-01 — Declarar `av` no requirements.** Bloqueador: instalação limpa não sobe.
2. **B-02 — Câmera virtual recebendo upscale de 640px.** Regressão de qualidade visível.
3. **B-05 — Suíte de testes do núcleo.** Pré-requisito pra encostar no detector.

---

## Bloqueios

- **Sem Python nesta máquina.** Só o stub da Microsoft Store. Os venvs `.venv/` e `venv/`
  apontam para `C:\Users\Computer\...\Python310` (outro PC) e estão mortos — apagar e
  recriar. Versão correta: **3.10.11** (é o que o `requirements.txt` declara).
- Enquanto isso, nada é executável nem testável localmente. Análise estática só.

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
