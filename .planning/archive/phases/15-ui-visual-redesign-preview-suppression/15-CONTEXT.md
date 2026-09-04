# Phase 15: UI Visual Redesign + Preview Suppression - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Aplicar dark mode consistente via QSS global, remover controles redundantes de VCam do painel Configurações Avançadas, e suprimir emissão de frames da engine ao minimizar a janela (somente no modo Automático). Sem novas features — é polish visual + uma otimização de CPU.

**Em escopo:**
- Criar `ui/styles.py` com `DARK_STYLESHEET` (QSS global — Streamer dark palette + hover states)
- Aplicar stylesheet via `app.setStyleSheet()` em `main.py`
- Remover VCam auto/manual toggle e Device VCam field de `geral_tab.py` (linhas ~180-217)
- Adicionar `_preview_suprimido` flag em `GestureEngine` + `set_preview_suprimido()` method
- Conectar `changeEvent` no window mixin para setar o flag ao minimizar (apenas em modo `"automatico"`)

**Fora de escopo:**
- Gesture card componentization (GestureCardWidget) — Phase 11 pode criar conforme necessário
- Novas features de câmera (CAM-05/06/07 completos) — Phase 13
- Onboarding dialog mudanças — Phase 14

</domain>

<decisions>
## Implementation Decisions

### Dark Theme — Implementação

- **D-01:** Abordagem QSS global via `setStyleSheet()` no `QApplication`. Zero novas dependências. Controle total sobre cada widget. Sem `qdarktheme` ou Qt Fusion palette.
- **D-02:** QSS centralizado em `ui/styles.py` como constante `DARK_STYLESHEET` (string Python). Carregado uma vez em `main.py`. Editar estilos não requer tocar em lógica de UI.
- **D-03:** Hover states via pseudo-classe `:hover` no QSS (troca instantânea de cor). Qt/QSS não tem `transition` nativo — sem `QPropertyAnimation`. Simples e sem overhead.

### Dark Theme — Paleta de Cores (Streamer dark)

- **D-04:** Paleta completa definida:
  ```
  Background:    #0d0d0d   (QMainWindow, QDialog)
  Surface:       #161616   (QTabWidget, QFrame, painéis)
  Border:        #2d2d2d   (bordas de widgets)
  Text:          #f0f0f0   (texto primário)
  Text muted:    #707070   (labels secundários, placeholders)
  Accent:        #7c4dff   (botão ativo/checkado, foco)
  Accent hover:  #9965ff   (botão hover no estado ativo)
  Button normal: #2a2a2a   (botão não-ativo background)
  Button hover:  #3a3a3a   (botão não-ativo hover)
  Danger:        #ff5252   (erros, status desconectado)
  Warning:       #ffab00   (avisos, latência alta)
  Success:       #69f0ae   (status conectado, latência boa)
  ```
- **D-05:** Botão `QPushButton` com estado `:checked` usa `background: #7c4dff; color: #ffffff`. Botões de modo (Teste/Manual/Automático) e seletor 1 Mão/2 Mãos seguem este padrão — já são `checkable`.

### Supressão do Preview

- **D-06:** Engine-level suppression: `GestureEngine.run()` pula `self.frame_ready.emit(frame)` quando `self._preview_suprimido is True`. Camera loop + MediaPipe + dispatch de ações continuam normalmente — apenas o frame não chega à UI.
- **D-07:** Setter público: `GestureEngine.set_preview_suprimido(valor: bool)`. Chamado pelo window mixin no `changeEvent`.
- **D-08:** `changeEvent` em `main_window.py` (ou `window_mixin.py` — o mixin que trata eventos de janela): detecta `QEvent.WindowStateChange`, checa `self.isMinimized()`, só chama `engine.set_preview_suprimido()` se engine estiver rodando e modo for `"automatico"`. Ao restaurar a janela, set `False`.
- **D-09:** Ao restaurar (unminimize), a engine retoma emissão de frames imediatamente no próximo ciclo do loop — sem lógica de warm-up.

### Limpeza de Configurações Avançadas

- **D-10:** Remover de `ui/tabs/geral_tab.py` os controles: `vcam_mode_group`, `vcam_auto_button`, `vcam_manual_button`, `vcam_device_edit`, `vcam_device_container`, `_vcam_device_container`, e o `adv_form.addRow("Câmera virtual:", ...)` / `adv_form.addRow("Device VCam:", ...)` (linhas ~180-217).
- **D-11:** Remover também os setters/getters de VCam do mixin de UI que façam referência a `vcam_device_edit` ou `vcam_mode` — ex.: `set_vcam_device()` e a lógica de leitura de `virtual_cam_mode`/`vcam_device` em `config_mixin.py` ou similar.
- **D-12:** O que **fica** no painel Configurações Avançadas: Resolução + FPS (os dois campos já existentes). O latency badge (fora do painel avançado, na aba Geral) permanece intocado.
- **D-13:** `config.json` — remover campos `virtual_cam_mode` e `vcam_device` se presentes. Migração silenciosa: na leitura, `.get("virtual_cam_mode", None)` simplesmente não é mais usado.

### Claude's Discretion

- Layout interno do `DARK_STYLESHEET` (ordem das regras QSS, quais widgets cobrir primeiro, padding/margin padrão dos tabs) — planner define.
- Nome exato do atributo de flag na engine (`_preview_suprimido` ou `_suppress_preview`) — manter padrão snake_case português do projeto.
- Ordem dos commits dentro da phase.

### Folded Todos

- **Todo:** "Suprimir preview da câmera ao minimizar janela (modo OBS ativo)" (`.planning/todos/pending/2026-06-27-suprimir-preview-ao-minimizar-em-modo-obs.md`) — dobrado. Decisões D-06 a D-09 resolvem integralmente o problema descrito.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos desta Phase
- `.planning/ROADMAP.md` §"Phase 15: UI Visual Redesign + Preview Suppression" — Goal + dependência de Phase 14
- `.planning/REQUIREMENTS.md` §"Categoria: UI Visual Redesign" — UI-01, UI-02, UI-03, UI-04
- `.planning/REQUIREMENTS.md` §"Categoria: Preview e Feedback Visual" — UX-05, UX-06 (somente na parte de suppression; overlay é Phase 12)

### Código afetado — UI / Estilos
- `ui/tabs/geral_tab.py` — todo o painel `advanced_panel` (linhas ~123-219); remover VCam rows; manter Resolução/FPS rows
- `ui/main_window.py` ou `ui/mixins/window_mixin.py` — `changeEvent` para detectar minimize/restore
- `main.py` — onde `QApplication` é criado; adicionar `app.setStyleSheet(DARK_STYLESHEET)`
- `ui/mixins/camera_mixin.py` — verificar se tem referências a `vcam_device_edit` ou `set_vcam_device()` para remover

### Código afetado — Engine
- `engine/gesture_engine.py` — `run()` método; adicionar guard `_preview_suprimido` antes de `frame_ready.emit()`; adicionar `set_preview_suprimido()` setter

### Contexto arquitetural
- `.planning/codebase/ARCHITECTURE.md` — §"Concurrency Model" (threads: main Qt, GestureEngine, gesture-actions)
- `.planning/phases/08-modos-de-opera-o/08-CONTEXT.md` — padrão de botões checkáveis em `geral_tab.py` (QPushButton + QButtonGroup) que o DARK_STYLESHEET deve estilizar

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `geral_tab.py:123-128` — `advanced_toggle` QPushButton com `setObjectName("ghost")` — padrão de botão toggle para QSS customizado
- `geral_tab.py:148-152` — `set_mode()` — padrão setter que conecta UI a config; `set_preview_suprimido()` na engine segue estrutura similar
- `geral_tab.py:287-297` — `update_latency_badge()` já usa `setStyleSheet()` inline por cor — depois do DARK_STYLESHEET global, revisar se usa variáveis da paleta ou sobrescreve corretamente
- `engine/gesture_engine.py:351-366` — loop principal onde `frame_ready.emit(frame)` ocorre; guard `_preview_suprimido` entra aqui
- `ui/mixins/camera_mixin.py` — já tem `_is_virtual_camera_name()` e `_populate_camera_devices()` — NÃO remover esses; só remover refs ao `vcam_device_edit`

### Established Patterns
- Botões de modo (`mode_test_button`, `mode_manual_button`, `mode_obs_button`) — `QPushButton(setCheckable(True))` + `QButtonGroup(setExclusive(True))` — padrão que DARK_STYLESHEET deve cobrir com `:checked` e `:hover`
- `config.get(key, default)` para todas as leituras de config — D-13 segue este padrão para remoção silenciosa
- Signals `frame_ready` e `status_changed` — engine → UI via Qt signals; suppression não altera o sinal, só quando é emitido

### Integration Points
- `main.py`: `QApplication` criado + `app.setStyleSheet()` adicionar logo após `app = QApplication(sys.argv)`
- `GestureEngine.run()`: único lugar onde `frame_ready.emit()` ocorre — guard entra aqui
- `main_window.py` `changeEvent`: ponto de entrada para eventos de janela (minimize, restore) — conectar à engine
- `geral_tab.py` `advanced_panel`: widget pai de todos os controles avançados; remover apenas as rows de VCam, não o painel inteiro

</code_context>

<specifics>
## Specific Ideas

- Identidade visual "Streamer dark" com roxo remete ao ecossistema Twitch/Discord — público-alvo de streamers vai reconhecer o padrão
- O latency badge usa `setStyleSheet()` inline por cor dinâmica — após o QSS global, confirmar que a cor dinâmica (verde/amarelo/vermelho) ainda prevalece (inline style tem maior especificidade que stylesheet global)
- Preview suppression é especialmente útil quando o streamer minimiza o app durante uma live longa — MediaPipe continua detectando gestos e executando ações sem desperdiçar CPU em render

</specifics>

<deferred>
## Deferred Ideas

### Gesture card componentization (GestureCardWidget)
- Explicitamente pulado: o usuário indicou que as phases de Combined Gesture (11+) estão fora do projeto por enquanto. Se Phase 11 voltar ao escopo, o planner pode extrair o widget então.

### Reviewed Todos (não dobrados)
- "Configurações de câmera → painel 'Configurações Avançadas' oculto" — Phase 14 (já resolvido parcialmente; a remoção de VCam nesta phase é complementar, não duplicada)
- "OBS Virtual Cam — modos automático e manual dentro de Configurações Avançadas" — **resolvido aqui** pela remoção (D-10/D-11): VCam é controlado exclusivamente pelo modo de operação
- "Detecção de 2 mãos e gestos combinados" — fora do escopo desta phase; Phase 9+ quando retomado
- "Modo automático como padrão de fábrica" — resolvido em Phase 8

</deferred>

---

*Phase: 15-UI Visual Redesign + Preview Suppression*
*Context gathered: 2026-07-01*
