# Phase 3: OBS Connection - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Tornar a conexão com o OBS confiável e não-bloqueante: o botão "Testar conexão" e o startup da engine nunca travam a UI, o estado da conexão é sempre visível independente da aba ativa, erros exibem mensagens acionáveis classificadas por tipo, e o status "conectado" só é definido após handshake confirmado via `get_version()`.

4 requirements em escopo: UX-04, OBS-01, UX-02, UX-03.

</domain>

<decisions>
## Implementation Decisions

### Arquitetura do thread de conexão OBS (UX-04)

- **D-01:** Criar `OBSConnectThread(QThread)` como classe reutilizável. Emite signals: `connected` (OBSController), `failed` (str com tipo de erro), `connecting`. Tanto o botão "Testar conexão" quanto o startup da engine usam essa mesma classe — sem duplicação de lógica de conexão.
- **D-02:** Thread criado por tentativa e destruído ao completar — não persiste entre tentativas. Sem fila de comandos. Quando o resultado chegar via signal, a main thread atualiza a UI.
- **D-03:** Durante a tentativa de conexão, a UI mostra: `test_obs_button.setEnabled(False)` + `obs_status_label.setText("Conectando...")`. Botão e label voltam ao estado normal (com resultado) ao completar.

### Handshake de verificação (OBS-01)

- **D-04:** `OBSController.connect()` chama `self.cliente.get_version()` após o construtor do `ReqClient` e antes de setar `self.connected = True`. Se `get_version()` lançar exceção, `connected` permanece `False`.

### Localização do indicador de status OBS (UX-02)

- **D-05:** Adicionar `QLabel` de status OBS na barra de rodapé da janela principal (`MainWindow`), ao lado do `status_label` existente ("Status: Rodando"). Exemplo: "🔴 OBS: Desconectado" / "🟢 OBS: Conectado" / "⏳ OBS: Conectando..." / "⚠️ OBS: Erro de senha". Visível em todas as abas sem mudança de layout.
- **D-06:** Manter os dois indicadores: rodapé (compacto, sempre visível) + `obs_status_label` na `OBSTab` (mensagem detalhada com instruções de o que fazer). São complementares: o rodapé resume, a aba OBS explica.

### Mensagens de erro acionáveis (UX-03)

- **D-07:** Cobrir 4 tipos de erro com mensagens específicas:
  - `ConnectionRefusedError` → "Conexão recusada — abra o OBS Studio e ative o WebSocket Server"
  - Erro de autenticação (senha) → "Senha incorreta — verifique as configurações do WebSocket no OBS"
  - `TimeoutError` → "Timeout — OBS não respondeu em 5s. Verifique o IP/porta"
  - `OSError`/host inválido (DNS failure) → "Endereço não encontrado — verifique o campo Host"
  - Outros erros → "Falha na conexão — verifique as configurações do WebSocket"
- **D-08:** Mensagem detalhada exibida no `obs_status_label` da `OBSTab`. Rodapé exibe versão resumida (ex: "⚠️ OBS: Senha incorreta"). Não usar `QMessageBox` — o fluxo natural já leva o usuário à aba OBS para corrigir.

### Claude's Discretion

- Classificação das exceções do `obsws-python`: usar `isinstance()` checks nos tipos de exceção da lib. Se a lib não expor tipos específicos de autenticação, fazer string matching no `str(exc)` como fallback — pesquisador deve verificar quais exceções a lib realmente levanta para os 4 cenários.
- Posicionamento do `QLabel` de status no rodapé: ao lado direito do `status_label` existente, separados por `|` ou espaçador — decisão de layout menor para o implementador.
- `OBSConnectThread` deve ser definido em `integrations/obs_controller.py` ou em novo arquivo `integrations/obs_connect_thread.py` — pesquisador decide com base nas convenções de módulo do projeto.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements desta Phase

- `.planning/ROADMAP.md` §"Phase 3: OBS Connection" — Goal + 5 Success Criteria que definem "done"
- `.planning/REQUIREMENTS.md` §"Conexão OBS" — UX-02, UX-03, UX-04, OBS-01 com especificações exatas

### Código afetado — OBS

- `integrations/obs_controller.py` — `OBSController` atual (30 linhas); D-04 adiciona `get_version()` aqui
- `ui/main_window.py:966–984` — `testar_conexao_obs()` — chamada bloqueante a ser substituída por `OBSConnectThread`
- `engine/gesture_engine.py:292–314` — `_connect_obs()` — a ser refatorado para usar `OBSConnectThread`

### Código afetado — UI

- `ui/tabs/obs_tab.py` — `obs_status_label` e `test_obs_button` (já existem; D-03 e D-08 operam neles)
- `ui/main_window.py` — rodapé da janela onde o novo QLabel de status OBS será adicionado (D-05); `status_label` já existe na linha ~532

### Análise de codebase

- `.planning/codebase/INTEGRATIONS.md` §"OBS Studio" — arquitetura atual de conexão, timeout, error handling
- `.planning/codebase/ARCHITECTURE.md` §"Concurrency Model" — tabela de threads (main, GestureEngine, gesture-actions)

### TODO pendente (não dobrado nesta phase)

- `.planning/todos/pending/2026-06-25-investigar-lag-em-resolu-es-altas-com-mediapipe-e-webcams.md` — investigação de lag em resoluções altas; escopo de engine (Phase 2+), não de conexão OBS

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `util/logger.py:get_logger()` — usar em `OBSConnectThread` para logging de tentativa/resultado
- `obs_status_label` em `OBSTab` — já existe; D-06 reutiliza para mensagem detalhada
- `health_obs` em `geral_tab.py` — já existe; pode ser atualizado via signal junto com o rodapé (D-05), mas não é o indicador principal
- `status_label` no rodapé de `MainWindow` — referência de posicionamento e padrão visual para o novo label de status OBS

### Established Patterns

- `GestureEngine(QThread)` com signals Qt — `OBSConnectThread` deve seguir o mesmo padrão: subclasse de `QThread`, override de `run()`, emite signals thread-safe
- `ThreadPoolExecutor(max_workers=1)` para ações OBS dentro da engine — `OBSConnectThread` é uma alternativa mais adequada para a tentativa de conexão inicial (resultado único, não recorrente)
- Error handling com `except Exception as exc` + `logger.exception()` — manter padrão no `OBSConnectThread`, mas adicionar classificação antes de emitir o signal `failed`

### Integration Points

- `OBSConnectThread.connected.emit(obs_controller)` → `MainWindow` atualiza `self.engine.obs`, `self.engine.actions.obs`, e os labels de status
- `OBSConnectThread.failed.emit(error_msg)` → `MainWindow` atualiza rodapé + `obs_status_label` na OBSTab
- `test_obs_button.clicked` → cria e inicia `OBSConnectThread` (substitui a chamada direta em `testar_conexao_obs()`)
- `GestureEngine._connect_obs()` → refatorar para criar e aguardar `OBSConnectThread` (ou delegar a chamada para a main thread via signal)

</code_context>

<specifics>
## Specific Ideas

- O pesquisador deve verificar empiricamente quais exceções o `obsws-python` lança para cada cenário de erro (senha errada, OBS fechado, timeout) — o `STATE.md` registra: "Testar comportamento de `obsws-python` em desconexão inesperada durante Phase 3." Esta verificação deve ser parte da pesquisa.
- Status no rodapé: usar emoji como prefixo de estado (🟢/🔴/⏳/⚠️) — visual intuitivo para streamers sem precisar de ícones externos.

</specifics>

<deferred>
## Deferred Ideas

- Reconexão automática ao OBS após queda de conexão em mid-session — explicitamente fora do escopo de v1.1 (listado em REQUIREMENTS.md §"v2 Requirements"). `OBSConnectThread` deve ser projetado de forma que um thread persistente (para reconexão) possa ser adicionado em v2 sem quebrar a arquitetura.

### Reviewed Todos (not folded)

- "Investigar lag em resoluções altas com MediaPipe e webcams" — escopo de engine/Phase 2, não relacionado à conexão OBS. Mantido em `.planning/todos/pending/` para Phase 4 ou investigação independente.

</deferred>

---

*Phase: 3-OBS Connection*
*Context gathered: 2026-06-24*
