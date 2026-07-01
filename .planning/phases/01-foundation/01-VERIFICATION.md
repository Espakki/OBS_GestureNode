---
phase: 01-foundation
verified: 2026-06-23T20:00:00-03:00
status: human_needed
score: 4/5 must-haves verified
behavior_unverified: 1
overrides_applied: 0
requirements_covered: [ENG-03, ENG-04, ENG-05, ENG-06, DEP-01, DEP-02]
must_haves_verified: 4/5
gaps: []
deferred: []
behavior_unverified_items:
  - truth: "Editar configurações em duas abas simultâneas não produz KeyError nem dispara a ação errada"
    test: "Iniciar o app, ligar a engine, alternar rapidamente entre abas Geral e Gestos editando campos por ~30s enquanto a câmera processa frames"
    expected: "Nenhum traceback de KeyError no console; gestos detectados disparam a ação do gesto correto"
    why_human: "A race condition só se manifesta com concorrência real UI+engine. grep e ast.parse comprovam que o RLock está presente e as properties estão corretas, mas não exercitam a interleaving real das threads. O SUMMARY documenta que o usuário aprovou a Task 3, porém essa aprovação foi capturada pelo executor durante a sessão de execução — a verificação formal precisa de confirmação explícita do developer."
human_verification:
  - test: "Edição concorrente de duas abas com engine rodando"
    expected: "Nenhum KeyError no console por ~30s de edição rápida de hold_time/cooldown/enabled enquanto a engine processa frames; gestos detectados acionam a ação correta"
    why_human: "Race condition só manifesta com concorrência real. A implementação (RLock, properties, _normalize_gesture_keys sob lock privado) está correta, mas o comportamento em runtime não é verificável estaticamente."
  - test: "Verificar se CR-01 (ROCK/TRES/QUATRO) afeta usuário na prática"
    expected: "Gestos Rock, Três e Quatro configurados com ação na UI deveriam disparar — se não dispararem, CR-01 está bloqueando. Isso está fora dos success criteria desta fase, mas o code review classifica como Critical."
    why_human: "O mismatch é confirmado estaticamente (ROCK->ROCK vs config key Rock), mas o impacto real depende de o usuário ter configurado esses gestos. A decisão de tratar como blocker ou defeito deferido para a próxima fase é do developer."
---

# Phase 01: Foundation — Verification Report

**Phase Goal:** O app inicializa sem erros em qualquer ambiente e o config.json nunca é corrompido
**Verified:** 2026-06-23T20:00:00-03:00
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | App iniciado via atalho carrega config.json corretamente (sem criar arquivo em system32) | VERIFIED | `main.py:12` define `CONFIG_PATH = Path(__file__).parent / "config.json"`; MainWindow instanciado com `config_path=CONFIG_PATH` (linha 35); `self._config_path` armazenado no `__init__` com fallback `Path(__file__).resolve().parent.parent`; `_do_save_config` usa `self._config_path.parent` para o tempfile — nunca o CWD |
| SC2 | Mover sliders por 10s não gera múltiplos arquivos temporários nem corrompe config.json | VERIFIED | `salvar_config_automatico()` chama apenas `self._save_timer.start(500)` (debounce); `_do_save_config()` usa `tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")` + `os.replace(tmp_path, str(self._config_path))` — write atômico confirmado; no exception path, unlink do .tmp é garantido; usuário confirmou Task 3 na sessão de execução |
| SC3 | `pip install -r requirements.txt` em ambiente limpo instala todas as dependências sem erros, incluindo pygrabber | VERIFIED | requirements.txt: 7 deps, todas com `==` exato, `pygrabber==0.2` presente, `mediapipe==0.10.14` intacto, sem linha inválida `python version`. Install em venv limpo confirmado pelo usuário (Task 3 do plano 01-01) |
| SC4 | Editar configurações em duas abas simultâneas não produz KeyError nem dispara a ação errada | PRESENT_BEHAVIOR_UNVERIFIED | `gesture_bindings` e `mapa_cenas` são properties que adquirem `threading.RLock()` em cada get/set; `_normalize_gesture_keys()` opera sobre atributos privados `_gesture_bindings`/`_mapa_cenas` sob um único `with self._bindings_lock:` (5 ocorrências verificadas); `_bindings_lock` inicializado antes de `_setup()`. O invariant de ausência de KeyError sob concorrência real é behavior-dependent — não verificável por grep |
| SC5 | `GESTURE_ALIASES` retorna o mesmo dicionário independente de qual módulo é consultado | VERIFIED | `core/gesture_aliases.py` exporta `GESTURE_ALIASES` (14 entradas, zero imports, zero funções); `gesture_detector.py`, `gesture_engine.py` e `main_window.py` todos contêm `from core.gesture_aliases import GESTURE_ALIASES` e nenhum tem `GESTURE_ALIASES = {`; identidade de objeto confirmada pelo usuário em Task 3 do plano 01-03 |

**Score:** 4/5 truths verified (1 present, behavior-unverified)

---

### Required Artifacts

| Artifact | Expected | Level 1 (Exists) | Level 2 (Substantive) | Level 3 (Wired) | Status |
|----------|----------|------------------|----------------------|-----------------|--------|
| `requirements.txt` | 7 deps pinadas com `==`, pygrabber e mediapipe | Exists | 7 deps, todos `==`, pygrabber==0.2, mediapipe==0.10.14, sem `python version` | Usado por pip install (validado pelo usuário) | VERIFIED |
| `config.json` (HEAD) | Template fresh install — bindings vazios, sem dados do dev | Exists | HEAD `af4ba74`: camera.index=0, device_name="", obs.host=localhost, todos `use_scene/use_sound/use_hotkey=false`, scene_map={}, sem path absoluto | Carregado por `carregar_config(caminho=CONFIG_PATH)` em main.py | VERIFIED |
| `core/gesture_aliases.py` | Fonte única de verdade, GESTURE_ALIASES dict 14 entradas | Exists | 14 entradas, zero imports, zero funções — verificado por ast.walk | Importado por gesture_detector, gesture_engine, main_window | VERIFIED |
| `engine/gesture_engine.py` | RLock + properties protegendo gesture_bindings e mapa_cenas | Exists | `import threading`, `self._bindings_lock = threading.RLock()`, properties com getter+setter, `_normalize_gesture_keys` sob lock privado | Properties usadas em `run()` via `self.gesture_bindings.get(...)`, setters chamados de main_window.py | VERIFIED |
| `main.py` | CONFIG_PATH via `__file__`, injetado em MainWindow | Exists | `from pathlib import Path`, `CONFIG_PATH = Path(__file__).parent / "config.json"`, `MainWindow(config, config_path=CONFIG_PATH)` | Passado para `MainWindow.__init__`, armazenado em `self._config_path` | VERIFIED |
| `ui/main_window.py` | Debounce 500ms + write atômico em `salvar_config_automatico` | Exists | `import tempfile`, `QTimer` importado, `_save_timer = QTimer(self)`, `setSingleShot(True)`, `_do_save_config` com `tempfile.mkstemp` + `os.replace`, sem `open("config.json")` literal | `_save_timer.timeout.connect(self._do_save_config)` no `__init__`; `salvar_config_automatico()` chama `_save_timer.start(500)`; `_do_save_config` usa `self._config_path` | VERIFIED |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.py` | `ui/main_window.py` | `MainWindow(config, config_path=CONFIG_PATH)` | WIRED | Linha 35 do main.py; `__init__` aceita `config_path` e armazena `self._config_path` |
| `ui/main_window.py salvar_config_automatico` | `config.json` | QTimer 500ms -> `_do_save_config` -> `os.replace(tmp, self._config_path)` | WIRED | `salvar_config_automatico` chama `_save_timer.start(500)`; timer conectado a `_do_save_config`; `_do_save_config` usa `tempfile.mkstemp` + `os.replace` |
| `engine/gesture_engine.py` | `core/gesture_aliases.py` | `from core.gesture_aliases import GESTURE_ALIASES` | WIRED | Import no topo do arquivo; usado em `_normalize_gesture_name()` linha 258 |
| `core/gesture_detector.py` | `core/gesture_aliases.py` | `from core.gesture_aliases import GESTURE_ALIASES` | WIRED | Import no topo; importado mas não usado diretamente (GESTURE_ALIASES disponível no namespace da classe) |
| `ui/main_window.py` | `engine/gesture_engine.py` | `self.engine.gesture_bindings = ...` aciona setter com lock | WIRED | 3 callsites em main_window.py atribuem via property setter que adquire `_bindings_lock` |

---

### Requirements Coverage

| REQ-ID | Plan | Description | Status | Evidence |
|--------|------|-------------|--------|---------|
| DEP-01 | 01-01 | `pygrabber` adicionado ao requirements.txt com versão fixada | SATISFIED | `pygrabber==0.2` em requirements.txt, linha 8 |
| DEP-02 | 01-01 | Todas as dependências com versões fixadas no requirements.txt | SATISFIED | 7 deps, todas com `==` exato, zero ranges `>=` ou `~=` |
| ENG-03 | 01-03 | `GESTURE_ALIASES` consolidado em `core/gesture_aliases.py` | SATISFIED | Módulo criado; 3 cópias locais removidas; todos os consumidores importam do módulo canônico |
| ENG-04 | 01-04 | Acesso a `gesture_bindings`/`mapa_cenas` protegido por `threading.RLock` | SATISFIED (code) | RLock inicializado antes de `_setup()`, properties com lock, `_normalize_gesture_keys` atômico sob lock privado; behavior em runtime via human verification |
| ENG-05 | 01-05 | Config carregado por caminho absoluto derivado de `__file__` | SATISFIED | `CONFIG_PATH = Path(__file__).parent / "config.json"` em main.py; injetado em MainWindow |
| ENG-06 | 01-05 | `salvar_config_automatico()` com debounce 500ms + write atômico | SATISFIED | QTimer single-shot 500ms + `tempfile.mkstemp` + `os.replace`; sem `open("config.json")` relativo |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `ui/main_window.py` `_do_save_config` | `self.config` | Dict populado em `__init__` e atualizado pelos handlers de UI | Sim — serializa o estado real da configuração para JSON | FLOWING |
| `main.py` `carregar_config` | retorno de `json.load(caminho)` | Leitura direta do arquivo via `CONFIG_PATH` absoluto | Sim — lê o JSON real do disco | FLOWING |
| `engine/gesture_engine.py` `gesture_bindings` | `_gesture_bindings` | Setter chamado de `_setup()` via `gestures_cfg.get("bindings", {})` e de main_window.py | Sim — dados reais do config, lidos do arquivo | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Evidence | Status |
|----------|----------|--------|
| `core/gesture_aliases.py` — módulo importável, 14 entradas, zero imports | `python -c "from core.gesture_aliases import GESTURE_ALIASES; assert len(GESTURE_ALIASES) == 14"` — PASS | PASS |
| `gesture_engine.py` — parse sem SyntaxError | `ast.parse` retornou sem exceção | PASS |
| `main.py` — `CONFIG_PATH` via `__file__`, injeção em MainWindow | grep confirmado programaticamente | PASS |
| `main_window.py` — debounce + atomic save presentes | `import tempfile`, `QTimer`, `os.replace`, `_save_timer.start(500)`, `def _do_save_config` todos confirmados via grep | PASS |
| GESTURE_ALIASES: 3 módulos importam do canônico, nenhum tem definição local | Verificado via ast.walk + grep — `GESTURE_ALIASES = {` ausente nos 3 arquivos | PASS |
| CR-01 confirmado: ROCK->ROCK, THREE->TRES, FOUR->QUATRO (não batem com ALL_GESTURES Rock/Três/Quatro) | `python -c "from core.gesture_aliases import GESTURE_ALIASES; ..."` — ROCK->ROCK (ALL_GESTURES tem 'Rock'), THREE->TRES (ALL_GESTURES tem 'Três'), FOUR->QUATRO (ALL_GESTURES tem 'Quatro') | DEFECT CONFIRMED |

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `core/gesture_aliases.py:10-12` | Valores `"ROCK"`, `"TRES"`, `"QUATRO"` não batem com chaves de `ALL_GESTURES` (`"Rock"`, `"Três"`, `"Quatro"`) | WARNING (CR-01 do code review) | 3 gestos (Rock, Três, Quatro) silenciosamente quebrados — `gesture_bindings.get("ROCK", {})` sempre retorna `{}`, impedindo que esses gestos disparem qualquer ação. Não é um TBD/FIXME nem corrupção de config, mas é um defeito introduzido pelo plano 01-03 que não foi detectado durante a execução. |
| `ui/main_window.py:1159` | `except OSError as exc` captura apenas IOError na camada externa; `TypeError` de `json.dump` (ex: valor não serializável no config) seria swallowed pelo Qt sem log | WARNING (CR-03 do code review) | Silenciosa perda de save em caso de objeto não-serializável no config. Improvável com os tipos atuais de config, mas frágil. |
| `ui/main_window.py:1045-1049` / `1113-1120` | Race condition em `restart_engine`: sinal `finished` da engine antiga pode null out a nova engine reference via `on_engine_finished` | WARNING (CR-02 do code review) | Narrow race — engine pode tornar-se não-parável sem reiniciar o app. Pré-existia ao Phase 1, não introduzido por ele. |

Nenhum marcador `TBD`, `FIXME`, ou `XXX` irresolvido encontrado nos arquivos modificados pela fase.

---

### config.json — Nota sobre Estado do Working Tree

O arquivo `config.json` no working tree contém dados de sessão do developer (bindings de "V" com `use_scene: true`, `scene: "Exemplo"`, `scene_map` não-vazio, `device_name: "HD Pro Webcam C920"`). Isso é **comportamento esperado**: o mecanismo ENG-06 (auto-save atômico) escreveu o estado da sessão de testes de verificação do usuário de volta ao arquivo. O `HEAD` commitado (`af4ba74`) contém o template limpo correto — verificado via `git show HEAD:config.json`. Não é uma regressão da implementação; é evidência de que o save está funcionando.

---

### Human Verification Required

#### 1. Edição Concorrente de Duas Abas (ENG-04 / SC4)

**Test:** Iniciar o app (`python main.py`), ligar a câmera/engine (modo test), alternar rapidamente entre as abas Geral e Gestos editando hold_time, cooldown, e habilitando/desabilitando gestos enquanto a engine processa frames. Fazer por ~30 segundos.
**Expected:** Nenhum traceback de `KeyError` no console; gestos detectados disparam a ação configurada corretamente (não de outro gesto).
**Why human:** A race condition entre main thread (escrita via UI) e engine thread (leitura no `run()`) só se manifesta com concorrência real. A implementação está correta (RLock, properties, `_normalize_gesture_keys` atômico), mas a ausência de KeyError em runtime não é verificável estaticamente. O SUMMARY.md documenta aprovação pelo usuário na Task 3, porém a verificação formal desta fase requer confirmação explícita do developer no contexto deste relatório.

**Nota:** O SUMMARY.md do plano 01-04 documenta que o usuário realizou este teste e não observou KeyError. Se o developer confirmar que a sessão de Task 3 cobriu este cenário adequadamente, esta human verification pode ser marcada como passed.

#### 2. Decisão sobre CR-01 (ROCK/TRES/QUATRO — defeito introduzido por esta fase)

**Test:** Configurar qualquer ação para os gestos Rock, Três ou Quatro na aba Gestos; executar a engine e realizar o gesto físico correspondente.
**Expected:** A ação configurada deveria disparar — se não disparar, CR-01 está bloqueando silenciosamente.
**Why human:** O defeito é confirmado estaticamente: `GESTURE_ALIASES` mapeia `ROCK->"ROCK"`, `THREE->"TRES"`, `FOUR->"QUATRO"`, mas as chaves em `gesture_bindings` (normalizadas de `ALL_GESTURES`) são `"Rock"`, `"Três"`, `"Quatro"`. O lookup sempre retorna `{}`. A decisão de tratar isso como blocker desta fase versus defeito a corrigir na próxima é do developer. A correção é trivial: ajustar 3 valores em `core/gesture_aliases.py` (`"ROCK"->"Rock"`, `"THREE"->"Três"`, `"FOUR"->"Quatro"`).

---

### Gaps Summary

Nenhum gap que bloqueie o goal da fase foi encontrado. Os 5 success criteria estão implementados no código:

- SC1 (config path via `__file__`): implementado e wired.
- SC2 (debounce + write atômico): implementado e wired.
- SC3 (requirements pinados + pygrabber): arquivo correto.
- SC4 (RLock para edição concorrente): implementado e wired; behavior em runtime human-needed.
- SC5 (GESTURE_ALIASES única fonte): implementado, wired, identidade verificada.

O CR-01 (ROCK/THREE/FOUR quebrados) é um **defeito introduzido por esta fase** que está fora do escopo dos success criteria, mas afeta a correção funcional de 3 dos 14 gestos. Requer decisão do developer (fix imediato ou deferir para Phase 2).

---

_Verified: 2026-06-23T20:00:00-03:00_
_Verifier: Claude (gsd-verifier)_
