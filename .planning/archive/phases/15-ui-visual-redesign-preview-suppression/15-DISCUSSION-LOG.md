# Phase 15: UI Visual Redesign + Preview Suppression - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-01
**Phase:** 15-ui-visual-redesign-preview-suppression
**Areas discussed:** Dark theme approach, Color palette, Preview suppression depth, Advanced Settings cleanup (user-initiated)

---

## Dark Theme — Implementação

| Option | Description | Selected |
|--------|-------------|----------|
| QSS global customizado | `setStyleSheet()` no QApplication com string/arquivo .qss. Zero dependências, controle total. | ✓ |
| qdarktheme (pip install) | Biblioteca pronta, uma linha de código. Adiciona dependência, menos controle. | |
| Qt Fusion palette | `app.setStyle('Fusion')` + QPalette. Sem deps, mas sem border-radius nem hover suave. | |

**User's choice:** QSS global customizado
**Notes:** Usuário preferiu não adicionar dependências e ter controle total sobre os estilos.

---

## Localização do QSS

| Option | Description | Selected |
|--------|-------------|----------|
| Arquivo `ui/styles.py` | Constante `DARK_STYLESHEET` em módulo dedicado. Carregado em main.py. | ✓ |
| Passar para supressão | Detalhe de localização deixado para o planner. | |

**User's choice:** `ui/styles.py`
**Notes:** Separação clara entre estilo e lógica.

---

## Paleta de Cores

| Option | Description | Selected |
|--------|-------------|----------|
| OBS-like (cinzas + verde) | Familiar para usuários de OBS. Cinzas neutros, acento verde. | |
| VS Code dark (cinzas + azul) | Paleta conhecida por devs. Tom frio, azul para ações primárias. | |
| Streamer dark (quase preto + roxo/âmbar) | Mais imersivo. Fundo #0d0d0d, diferenciado. | ✓ |

**User's choice:** Streamer dark

---

## Cor de Acento

| Option | Description | Selected |
|--------|-------------|----------|
| Roxo #7c4dff | Remete a Twitch/Discord, criativo. | ✓ |
| Âmbar #ffab00 | Mais quente, menos saturado. | |

**User's choice:** Roxo #7c4dff
**Notes:** Público-alvo são streamers — paleta remete ao ecossistema Twitch/Discord.

---

## Hover States / Transições

| Option | Description | Selected |
|--------|-------------|----------|
| QSS :hover puro | Troca instantânea via pseudo-classe `:hover`. Zero overhead. | ✓ |
| QPropertyAnimation (~150ms) | Fade suave via animação Python. Mais código, mais manutenção. | |

**User's choice:** QSS :hover puro
**Notes:** Qt/QSS não tem `transition` nativo; troca instantânea de cor com a paleta certa é suficiente.

---

## Supressão do Preview — Profundidade

| Option | Description | Selected |
|--------|-------------|----------|
| Engine-level (parar emit) | `frame_ready.emit()` pulado quando minimizado. Camera + MediaPipe + ações continuam. | ✓ |
| UI-level (ignorar frames) | Engine emite normalmente; QLabel pula `setPixmap()`. CPU de encode não economizada. | |

**User's choice:** Engine-level
**Notes:** Melhor trade-off — gestos funcionam normalmente (útil durante live), render economizado.

---

## Configurações Avançadas — Limpeza

**Contexto (user-initiated):** Usuário identificou que os controles de VCam (auto/manual e Device VCam) são redundantes com o Modo de Operação (que já controla se VCam está ativo ou não). Pediu remoção durante a seleção de áreas.

**Decisão:** Remover de `geral_tab.py` os widgets `vcam_mode_group`, `vcam_auto_button`, `vcam_manual_button`, `vcam_device_edit`, `vcam_device_container`. Manter Resolução, FPS e latency badge.

**O que fica:** Resolução + FPS (enumeração de câmera) + latency badge (fora do painel avançado).

---

## Claude's Discretion

- Layout interno do `DARK_STYLESHEET` (ordem das regras QSS, quais widgets cobrir primeiro)
- Padding/margin padrão de tabs e painéis
- Nome exato do flag de supressão na engine (`_preview_suprimido` sugerido, planner confirma)
- Ordem dos commits dentro da phase

## Deferred Ideas

- **Gesture card componentization (GestureCardWidget):** Explicitamente pulado — usuário indicou que as phases de Combined Gesture estão fora do projeto por enquanto.
- **Phases 9-14 adiadas:** Usuário confirmou que phases intermediárias (gestos combinados, etc.) não são prioridade. Phase 15 foi puxada para execução direta.
