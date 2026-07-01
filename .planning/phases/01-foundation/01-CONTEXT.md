# Phase 1: Foundation - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Corrigir os 5 defeitos críticos (ENG-03, ENG-04, ENG-05, ENG-06) e reparar as dependências quebradas (DEP-01, DEP-02). O app deve inicializar sem erros em qualquer ambiente e o config.json nunca deve ser corrompido. Nenhuma feature nova — estabilização pura.

</domain>

<decisions>
## Implementation Decisions

### config.json no Repositório
- **D-01:** Commitar config.json limpo — estrutura correta com todos os campos, mas sem paths absolutos do developer e sem placeholders de hotkey ("Pressione as teclas..."). O arquivo permanece rastreado no git como referência de desenvolvimento.
- **D-02:** Gestos com bindings vazios (sem ações configuradas) — sem exemplos pré-preenchidos. Consistente com o comportamento do .exe: na primeira execução o usuário final sempre parte de um config fresh.

### Pinagem de Dependências (DEP-02)
- **D-03:** Pesquisador busca as versões estáveis mais recentes de cada pacote compatíveis com Python 3.10.11 e pina com `==`. Estratégia: máxima estabilidade sem necessidade de rodar `pip freeze` manualmente.
- **D-04:** `mediapipe==0.10.14` permanece pinado exatamente — não alterar por nenhuma razão nesta fase.
- **D-05:** `pygrabber==0.2` — versão exata (única versão disponível no PyPI; projeto estável sem updates).
- **D-06:** A linha inválida `python version == 3.10.11` é removida do requirements.txt e substituída por comentário `# Python 3.10.11`.

### GESTURE_ALIASES — Consolidação (ENG-03)
- **D-07:** Criar `core/gesture_aliases.py` como arquivo separado — fonte única de verdade. Todos os módulos importam deste arquivo.
- **D-08:** Conteúdo: apenas o dict `GESTURE_ALIASES`, sem funções helper. Exemplo: `GESTURE_ALIASES = {"open_palm": "Mão Aberta", ...}`.
- **D-09:** O dict canônico inclui TODOS os gestos como união das 3 cópias divergidas — incluindo `"V": "V"` que estava faltando em uma das cópias. As cópias locais em `gesture_detector.py`, `gesture_engine.py` e `main_window.py` são removidas e substituídas por `from core.gesture_aliases import GESTURE_ALIASES`.

### HotkeyListener
- **D-10:** [informational] `util/hotkey_listener.py` é mantido sem alteração na Phase 1. Será integrado na aba de configuração de gestos na Phase 5 (UX-07).

### Claude's Discretion
- **Debounce do auto-save (ENG-06):** Usar `QTimer.singleShot(500, ...)` na thread principal do Qt — mais seguro e integrado ao lifecycle Qt do que `threading.Timer`. A chamada que chega de qualquer thread emite um signal para a main thread ativar o timer.
- **Lock threading (ENG-04):** Usar `threading.RLock` (permite reentrada) para proteger `gesture_bindings` e `mapa_cenas`. Mais seguro que `Lock` simples dado o padrão de acesso existente.
- **Config path (ENG-05):** Usar `Path(__file__).parent / "config.json"` no `main.py` (ou `parent.parent` dependendo da estrutura) — derivado de `__file__` do módulo, independente do CWD.
- **Write atômico (ENG-06):** Escrever em arquivo temporário na mesma partição e usar `os.replace()` para substituição atômica — proteção contra corrupção em crash.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos da Phase 1
- `.planning/REQUIREMENTS.md` §"Engine Foundation" — 6 requisitos com especificações exatas (ENG-03, ENG-04, ENG-05, ENG-06, DEP-01, DEP-02)
- `.planning/ROADMAP.md` §"Phase 1: Foundation" — Goal e 5 Success Criteria que definem "done"

### Análise da Codebase
- `.planning/codebase/CONCERNS.md` — Itens específicos que cada requisito resolve (race condition, config path, debounce, pygrabber ausente, GESTURE_ALIASES duplicado)
- `.planning/codebase/STACK.md` — Dependências atuais e seus riscos de versão

### Arquivos de Código Afetados
- `core/gesture_detector.py` — contém uma cópia do GESTURE_ALIASES (remover)
- `engine/gesture_engine.py` — contém uma cópia do GESTURE_ALIASES (remover); lê `gesture_bindings` sem lock
- `ui/main_window.py` — contém uma cópia do GESTURE_ALIASES (remover); escreve `gesture_bindings` sem lock; chama `salvar_config_automatico()` sem debounce
- `main.py` — carrega config.json com caminho relativo (corrigir para absoluto via `__file__`)
- `util/hotkey_listener.py` — manter sem alteração

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `util/logger.py:get_logger()` — já existe e deve ser usado para substituir `print()` em `CameraManager` (limpeza de oportunidade, não bloqueante para esta fase)
- `util/hotkey_listener.py` — implementação existente de captura de hotkeys, reservada para Phase 5

### Established Patterns
- Configuração centralizada em dict `config` (carregado em `main.py`, passado para `MainWindow`) — ENG-05 e ENG-06 operam dentro deste padrão existente
- `GestureEngine(QThread)` com signals Qt — ENG-04 adiciona lock sem alterar o padrão de threading existente
- `UPPER_SNAKE_CASE` para dicts de módulo — `core/gesture_aliases.py` segue esta convenção

### Integration Points
- `core/gesture_aliases.py` novo → importado por `gesture_detector.py`, `gesture_engine.py`, `main_window.py`
- `threading.RLock` adicionado como atributo de `GestureEngine` → wraps nos accessores de `gesture_bindings` e `mapa_cenas`
- `QTimer.singleShot` para debounce → wired no `MainWindow.__init__` ou via signal para garantir execução na main thread

</code_context>

<specifics>
## Specific Ideas

- O config.json de template no repo deve representar o estado de "app recém instalado": câmera padrão, modo "test", OBS com valores padrão de host/porta, gestos presentes mas sem ações configuradas.
- O pesquisador deve verificar compatibilidade de cada versão pinada com Python 3.10.11 antes de propor — especialmente `pyvirtualcam` que tem histórico de breaking changes.

</specifics>

<deferred>
## Deferred Ideas

- Correção do `bare except:` em `util/hotkey_listener.py` — mencionado no CONCERNS.md mas não explicitamente em nenhum requisito da Phase 1. Adiar para Phase 5 quando o arquivo for integrado.
- Substituição de `print()` por `get_logger()` em `CameraManager` — melhoria de qualidade válida, mas fora do escopo estrito da Phase 1. Adiar para Phase 2 (onde CameraManager é central).
- Dual config sources (in-memory dict vs. engine attributes) — problema arquitetural maior, não adequado para esta fase de Foundation que foca em correções cirúrgicas.

</deferred>

---

*Phase: 1-Foundation*
*Context gathered: 2026-06-22*
