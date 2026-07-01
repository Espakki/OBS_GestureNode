# Phase 8: Modos de Operação - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Adicionar o 3º modo (Manual), renomear "OBS" → "Automático", e atribuir comportamentos distintos de WebSocket e VCam a cada modo. A seleção persiste no config.json. Nenhuma feature nova além dos modos em si — configurabilidade de VCam e Camera Settings ficam na Phase 13.

**Matriz de comportamento (resultado desta discussão):**

| Modo | WebSocket OBS | VCam (pyvirtualcam) | Hotkeys/Áudio |
|------|---------------|---------------------|---------------|
| Teste | ❌ | ❌ | ❌ |
| Manual | ✅ auto | ❌ | ✅ |
| Automático | ✅ auto | ✅ | ✅ |

</domain>

<decisions>
## Implementation Decisions

### Padrão de Fábrica
- **D-01:** Padrão de fábrica é `"automatico"` (não `"teste"`). O todo `modo-automatico-como-padrao-de-fabrica.md` e o STATE.md sobrepõem MODE-04 do REQUIREMENTS.md. Engine já tolera OBS ausente sem crash (Phase 3 via OBSConnectThread), portanto sem risco funcional. SC5 do roadmap ("primeira execução em Teste") fica substituída por esta decisão.

### Modo Teste — Escopo de Bloqueio
- **D-02:** Modo Teste bloqueia **todas** as ações: sem OBS, sem hotkeys, sem áudio. Sandbox puro para calibrar gestos.
- **D-03:** Ao iniciar a engine em modo Teste, a UI exibe mensagem clara informando o bloqueio (ex: status bar: "Modo Teste — ações desativadas"). Não usar modal — mensagem passiva e persistente enquanto o modo estiver ativo.
- **Mudança vs. v1.1:** v1.1 test mode ainda disparava hotkeys/áudio. Agora bloqueia tudo. Checar em `ActionManager.executar()` e nas saídas de hotkey.

### Modo Manual — Comportamento
- **D-04:** Manual = auto-conecta WebSocket OBS ao iniciar (igual ao Automático) + sem VCam. A única diferença entre Manual e Automático é que o pyvirtualcam não inicia.
- **D-06:** O botão "Conectar OBS" na aba OBS continua funcionando em Manual para reconexão manual em caso de queda — não é o gatilho da conexão inicial (que é automática).

### Claude's Discretion

- **D-05:** User story do Manual: power user com problema de driver de VCam (conflito, device incompatível) — fallback técnico quando o modo Automático não é viável. Não é modo intermediário de onboarding. Comportamento já capturado por D-04; nenhuma implementação adicional requerida.

### Layout e Labels da UI
- **D-07:** 3 `QPushButton` checkáveis em linha horizontal — expande o padrão atual de `geral_tab.py:48-56`. Sem mudança de widget type.
- **D-08:** Labels: **Teste | Manual | Automático** (sem alteração de nomes). Tooltips e `mode_help_label` atualizar para descrever os 3 modos com seus comportamentos.
- **D-09:** Valores internos do config.json: `"teste"`, `"manual"`, `"automatico"` (string simples, snake_case sem acento — consistente com o padrão existente `"test"` → renomear para `"teste"`).

### Folded Todos
- **Todo:** "Modo automático como padrão de fábrica" (`.planning/todos/pending/2026-06-27-modo-automatico-como-padrao-de-fabrica.md`) — dobrado. Decisão D-01 resolve integralmente o problema descrito.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos desta Phase
- `.planning/ROADMAP.md` §"Phase 8: Modos de Operação" — Goal + 5 Success Criteria (NOTE: SC5 substituída pela decisão D-01)
- `.planning/REQUIREMENTS.md` §"Categoria: Modos de Operação" — MODE-01, MODE-02, MODE-03, MODE-04 (NOTE: MODE-04 padrão substituído por D-01)

### Código afetado — Engine
- `engine/gesture_engine.py:299` — `_connect_obs()` atualmente checa `modo == "obs"` — atualizar para `"automatico"` e `"manual"`
- `engine/gesture_engine.py:228-229` — `enable_virtual_camera` passado para CameraManager — controlar por modo
- `actions/action_manager.py` — `executar()` precisa checar modo antes de disparar hotkeys/áudio (nova lógica para D-02)

### Código afetado — UI
- `ui/tabs/geral_tab.py:42-72` — `mode_group`, `mode_test_button`, `mode_obs_button`, `mode_help_label` — adicionar 3º botão, atualizar textos
- `ui/tabs/geral_tab.py:148-152` — `set_mode()` — atualizar para 3 modos
- `ui/main_window.py:115` — `config.setdefault("modo", "test")` — atualizar para `"automatico"` (D-01) e `"teste"` (D-09)
- `ui/main_window.py:455-456` — conexão de signals `toggled` — adicionar 3º signal para modo `"manual"`
- `ui/main_window.py:936-939` — `on_modo_changed()` — lógica de VCam por modo (D-04)
- `ui/main_window.py:1130-1135` e `:1293-1313` — verificações de modo OBS no status/health — atualizar para 3 modos

### Contexto arquitetural
- `.planning/codebase/ARCHITECTURE.md` §"Concurrency Model" — tabela de threads (main, GestureEngine, gesture-actions)
- `.planning/phases/03-obs-connection/03-CONTEXT.md` — padrão `OBSConnectThread` (reutilizado pelos modos Manual e Automático)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OBSConnectThread` em `integrations/obs_connect_thread.py` — já implementado na Phase 3; Manual e Automático reutilizam sem alteração para auto-connect
- `geral_tab.py:mode_group` (QButtonGroup) — suporta N botões; adicionar `mode_manual_button` segue o padrão existente
- `geral_tab.py:mode_help_label` — widget já existente para texto descritivo abaixo dos botões; atualizar texto para 3 modos

### Established Patterns
- Modo persistido em `config["modo"]` como string — padrão mantido; só adicionar valor `"manual"` e renomear `"test"` → `"teste"`
- `on_modo_changed(modo)` em `main_window.py:936` — entry point único para mudança de modo; toda lógica de comportamento entra aqui
- `config.setdefault()` em `main_window.py:115+` — padrão de migração silenciosa; adicionar defaults para novo campo sem quebrar configs v1.1

### Integration Points
- `ActionManager.executar()` → recebe `config` ou referência ao modo; precisa de acesso ao modo atual para bloqueio no Teste (D-02)
- `CameraManager` ← `enable_virtual_camera` boolean passado no construtor; Phase 8 define QUANDO esse bool é True (só no Automático)
- `main_window.py:1293-1313` → `_validar_config()` e health labels leem `modo` — atualizar condicionais `modo == "obs"` para novos valores

### Migração de config v1.1 → v1.2
- `"modo": "test"` (v1.1) → deve ser tratado como `"teste"` (v1.2) na leitura (migration silenciosa via `.get()` com mapeamento)
- `"modo": "obs"` (v1.1) → tratar como `"automatico"` na migração

</code_context>

<specifics>
## Specific Ideas

- Mensagem de "Modo Teste — ações desativadas" deve aparecer no status bar da engine (label de status existente), não como modal nem tooltip — passiva e persistente (D-03).
- O `mode_help_label` abaixo dos botões deve descrever o comportamento de cada modo de forma orientada ao streamer — ex: "Automático: câmera virtual e OBS gerenciados automaticamente."

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded — routed to correct phases)
- "Configurações de câmera → painel 'Configurações Avançadas' oculto" — Phase 14 (resolves_phase: 14 confirmado)
- "OBS Virtual Cam — modos automático e manual dentro de Configurações Avançadas" — Phase 13 (configurabilidade do VCam, não comportamento por modo)
- "Suprimir preview da câmera ao minimizar janela (modo OBS ativo)" — Phase 15 (resolves_phase: 15 confirmado)
- "Detecção de 2 mãos e gestos combinados" — Phase 9 (resolves_phase: 9 confirmado)

</deferred>

---

*Phase: 8-Modos de Operação*
*Context gathered: 2026-06-27*
