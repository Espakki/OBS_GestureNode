# Phase 9: HandTracker API Refactor - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Refatorar `HandTracker.processar()` para retornar `list[dict]` — um dict por mão detectada, com landmarks e handedness correto (inversão aplicada para frames pré-espelhados). Atualizar `GestureEngine` atomicamente para consumir a nova API com estado per-hand (`detection_window`, `stability_monitor`, `gesto_ativo`, `inicio_gesto`) e dispatch independente por mão. Adicionar seletor "1 Mão / 2 Mãos" na aba Geral. Nenhuma regressão de 1 mão.

**Fora de escopo desta fase:**
- Gestos COMBINADOS (par esquerda+direita como unidade) → Phase 10
- Config schema v2 completo com `combined_bindings` → Phase 10
- Preview overlay com 2 barras de hold time → Phase 12
- Bindings separadas por mão (left_thumbs_up vs right_thumbs_up) → Phase 10/11

</domain>

<decisions>
## Implementation Decisions

### Novo retorno de HandTracker.processar()
- **D-01:** `processar()` retorna `(frame_small, list[dict])` onde cada dict tem:
  ```python
  {"landmarks": list[tuple[int,int]],  # 21 pontos (px, py) na escala do frame processado
   "handedness": "Left" | "Right"}      # handedness físico já com inversão aplicada
  ```
  Lista vazia `[]` quando nenhuma mão detectada (substitui `pontos = []` atual).
- **D-02 (fixo — pitfall documentado):** Handedness invertido na saída: MediaPipe "Right" em frame pré-espelhado = mão física esquerda. Fix aplicado em `HandTracker.processar()` — inverte o label antes de retornar. GestureEngine recebe handedness fisicamente correto, sem lógica extra de inversão.
- **D-03:** `max_num_hands` controlado por parâmetro no construtor de `HandTracker` — não hardcoded. GestureEngine lê `config.get("max_maos", 1)` e instancia `HandTracker(max_num_hands=max_maos)`.

### Dispatch de ações no modo 2 mãos
- **D-04:** Cada mão detecta e dispara sua própria binding **independentemente** usando o mesmo pool de bindings da config existente. Thumbs_up na mão esquerda OU direita → mesma ação configurada. Zero migração de config necessária.
- **D-05:** Cooldown **compartilhado por gesto** entre mãos — `ultimo_disparo_por_gesto` é um dict único (não per-hand). Se thumbs_up disparou em qualquer mão, ambas as mãos ficam bloqueadas pelo cooldown ("primeira mão vence"). Evita duplo-disparo acidental.
- **D-06:** Estado per-hand no GestureEngine para 2 mãos: `detection_window`, `stability_monitor`, `gesto_ativo`, `inicio_gesto` — um conjunto por mão, indexado por handedness ("Left", "Right"). `ultimo_disparo_por_gesto` permanece compartilhado (D-05).

### Widget "1 Mão / 2 Mãos" na aba Geral
- **D-07:** 2 `QPushButton` checkáveis em linha horizontal — mesmo padrão dos botões Teste/Manual/Automático em `geral_tab.py:42-56`. Label: `1 Mão` | `2 Mãos`.
- **D-08:** Posicionamento: **logo abaixo do row de modo** (Teste/Manual/Automático). Agrupa controles de operação juntos.
- **D-09:** Config key: `config["max_maos"]` (int: 1 ou 2). Default: 1. Leitura com `.get("max_maos", 1)` — sem migração, configs v1.1 carregam silenciosamente em modo 1 mão.

### Restart ao trocar 1↔2 mãos
- **D-10:** Engine **rodando** + troca 1↔2 mãos → **auto-restart automático**: engine para (`stop()`) + reinicia (`start()`) com novo valor de `max_maos`. Status emite "Reiniciando..." durante a transição. Mesmo padrão de restart já usado ao trocar câmera em `main_window.py`.
- **D-11:** Engine **parada** + troca 1↔2 mãos → persiste `max_maos` no `config.json` imediatamente; aplica no próximo `Start`. Sem restart desnecessário.

### Constraint de performance (fixo — documentado)
- **D-12 (fixo):** `model_complexity=0` obrigatório em modo 2 mãos para manter 20-28 FPS. `HandTracker.__init__` já usa `model_complexity=0` — sem mudança necessária. Documentar no smoke test que FPS em 2 mãos deve ser medido durante Phase 9.

### Folded Todos
- **Todo:** "Detecção de 2 mãos e gestos combinados" (`.planning/todos/pending/2026-06-26-deteccao-de-2-maos-e-gestos-combinados.md`) — porção de Phase 9 dobrada. Cobre HandTracker API refactor + per-hand dispatch. Gestos combinados (par) ficam em Phase 10 conforme planejado.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos desta Phase
- `.planning/ROADMAP.md` §"Phase 9: HandTracker API Refactor" — Goal + 3 Success Criteria + nota CRITICAL de commit atômico
- `.planning/REQUIREMENTS.md` §"Categoria: Detecção de 2 Mãos" — GES-01, GES-02 (os dois únicos requisitos desta phase)

### Pitfalls críticos — LEITURA OBRIGATÓRIA
- `.planning/research/SUMMARY.md` — 5 pitfalls v1.2 documentados; os de Phase 9 são: flat landmark list (P-01), GestureStabilityMonitor por mão (P-02), handedness invertido (P-03)

### Código afetado — HandTracker
- `core/hand_tracker.py:11-54` — classe `HandTracker` inteira; `processar()` é o único método público; retorno atual é `(frame_small, pontos_flat)`
- `core/hand_tracker.py:18-23` — `Hands(max_num_hands=1, ...)` — hardcoded a ser parametrizado

### Código afetado — GestureEngine
- `engine/gesture_engine.py:155-504` — classe `GestureEngine` inteira
- `engine/gesture_engine.py:209-213` — `GestureStabilityMonitor` instância única (`self.stability_monitor`) — refatorar para dict per-hand
- `engine/gesture_engine.py:242` — `self.tracker = HandTracker()` — passar `max_num_hands`
- `engine/gesture_engine.py:351-366` — loop principal: `pontos = tracker.processar(...)` + `detector.detectar(pontos)` — refatorar para iterar `list[dict]`
- `engine/gesture_engine.py:370-379` — `gesto_ativo`, `inicio_gesto`, `stability_monitor.reset()` — refatorar para per-hand
- `engine/gesture_engine.py:21-152` — `GestureStabilityMonitor` classe — sem mudança na classe, mas instanciação muda

### Código afetado — UI
- `ui/tabs/geral_tab.py:42-72` — row de modo (Teste/Manual/Automático); novo row "1 Mão / 2 Mãos" entra logo abaixo seguindo o mesmo padrão
- `ui/main_window.py` — wiring do novo seletor; lógica de auto-restart ao trocar max_maos

### Contexto arquitetural
- `.planning/codebase/ARCHITECTURE.md` §"Data Flow" — fluxo Camera→Action, passo 2 (HandTracker) e passo 3 (GestureDetector)
- `.planning/phases/08-modos-de-opera-o/08-CONTEXT.md` — padrão de 2 QPushButtons em `geral_tab.py` (D-07) e padrão de restart via `main_window.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GestureStabilityMonitor` (gesture_engine.py:21-152) — classe sem mudança; apenas instanciar uma por mão em vez de uma global. Método `reset()` chamado ao trocar de gesto permanece idêntico.
- `geral_tab.py:42-72` — QButtonGroup + 2 QPushButtons checkáveis — copiar padrão exato para o row "1 Mão / 2 Mãos"
- `geral_tab.py:148-152` — `set_mode()` — padrão de setter para o novo `set_max_maos()`
- `main_window.py` — lógica de restart da engine ao trocar câmera — reutilizar para auto-restart ao trocar max_maos (D-10)

### Established Patterns
- Retorno `(frame, data)` de `HandTracker.processar()` — manter tupla, apenas mudar tipo de `data`: `list[tuple]` → `list[dict]`
- `resultado.multi_hand_landmarks` + `resultado.multi_handedness` do MediaPipe — já disponíveis no resultado de `self.maos.process(frame_rgb)`; `multi_handedness[i].classification[0].label` retorna "Left" ou "Right" (a inverter)
- `deque(maxlen=N)` para detection_window — manter padrão, um deque por mão indexado por string "Left"/"Right"
- Config key via `.get(key, default)` — D-09 segue este padrão (`.get("max_maos", 1)`)

### Integration Points
- `GestureDetector.detectar(pontos)` — assinatura NÃO muda nesta phase; engine extrai `hand["landmarks"]` e chama `detectar()` por mão
- `frame_ready.emit(frame)` — continua emitindo um frame único anotado (skeleton de ambas as mãos no frame_small)
- `status_changed.emit(str)` — continua emitindo string de status; em 2 mãos pode emitir "Gesto Left: thumbs_up | Right: open_palm" (implementação a critério do planner)

### Constraint de commit atômico
- `hand_tracker.py` e `gesture_engine.py` DEVEM ser commitados no mesmo commit — API quebra engine se atualizados independentemente. Um único plano deve cobrir ambos os arquivos.

</code_context>

<specifics>
## Specific Ideas

- Smoke test obrigatório (de STATE.md §Todos): "Levantar mão direita → confirmar label 'Right' no preview; mão esquerda → 'Left'" — deve ser o primeiro teste após execução
- Medir FPS em modo 2 mãos durante Phase 9: estimativa 20-28 FPS (documentar se < 20 FPS em hardware low-end)
- Labels de handedness no preview devem aparecer como parte do skeleton existente ou como texto no frame — não como UI overlay (que é escopo da Phase 12)

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (não dobrados — roteados para phases corretas)
- "Configurações de câmera → painel 'Configurações Avançadas' oculto" → Phase 14 confirmado
- "Modo automático como padrão de fábrica" → resolvido na Phase 8 (D-01 de 08-CONTEXT.md)
- "OBS Virtual Cam — modos automático e manual dentro de Configurações Avançadas" → Phase 13 confirmado
- "Suprimir preview da câmera ao minimizar janela (modo OBS ativo)" → Phase 15 confirmado

### Gestos combinados (par esquerda+direita)
- Dispatch de par como unidade (ambas as mãos mantêm gestos por hold_time completo) → Phase 10
- Config schema `combined_bindings` + `config_version: 2` → Phase 10 (GES-06, GES-07)
- Bindings separadas por mão (left_thumbs_up ≠ right_thumbs_up) → Phase 10/11

</deferred>

---

*Phase: 9-HandTracker API Refactor*
*Context gathered: 2026-06-27*
