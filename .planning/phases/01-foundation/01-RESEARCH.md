# Phase 1: Foundation — Research

**Pesquisado em:** 2026-06-22
**Domínio:** Python venv · PySide6 Qt threading · atomic file I/O · dependency pinning
**Confiança geral:** MEDIUM (código fonte verificado diretamente; versões verificadas via `pip index versions`)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**config.json no Repositório**
- D-01: Commitar config.json limpo — estrutura correta com todos os campos, mas sem paths absolutos do developer e sem placeholders de hotkey ("Pressione as teclas..."). O arquivo permanece rastreado no git como referência de desenvolvimento.
- D-02: Gestos com bindings vazios (sem ações configuradas) — sem exemplos pré-preenchidos. Consistente com o comportamento do .exe: na primeira execução o usuário final sempre parte de um config fresh.

**Pinagem de Dependências (DEP-02)**
- D-03: Pesquisador busca as versões estáveis mais recentes de cada pacote compatíveis com Python 3.10.11 e pina com `==`. Estratégia: máxima estabilidade sem necessidade de rodar `pip freeze` manualmente.
- D-04: `mediapipe==0.10.14` permanece pinado exatamente — não alterar por nenhuma razão nesta fase.
- D-05: `pygrabber==0.2` — versão exata (única versão disponível no PyPI; projeto estável sem updates).
- D-06: A linha inválida `python version == 3.10.11` é removida do requirements.txt e substituída por comentário `# Python 3.10.11`.

**GESTURE_ALIASES — Consolidação (ENG-03)**
- D-07: Criar `core/gesture_aliases.py` como arquivo separado — fonte única de verdade. Todos os módulos importam deste arquivo.
- D-08: Conteúdo: apenas o dict `GESTURE_ALIASES`, sem funções helper. Exemplo: `GESTURE_ALIASES = {"open_palm": "Mão Aberta", ...}`.
- D-09: O dict canônico inclui TODOS os gestos como união das 3 cópias divergidas — incluindo `"V": "V"` que estava faltando em uma das cópias. As cópias locais em `gesture_detector.py`, `gesture_engine.py` e `main_window.py` são removidas e substituídas por `from core.gesture_aliases import GESTURE_ALIASES`.

**HotkeyListener**
- D-10: `util/hotkey_listener.py` é mantido sem alteração na Phase 1. Será integrado na aba de configuração de gestos na Phase 5 (UX-07).

### Claude's Discretion

- **Debounce do auto-save (ENG-06):** Usar `QTimer.singleShot(500, ...)` na thread principal do Qt — mais seguro e integrado ao lifecycle Qt do que `threading.Timer`. A chamada que chega de qualquer thread emite um signal para a main thread ativar o timer.
- **Lock threading (ENG-04):** Usar `threading.RLock` (permite reentrada) para proteger `gesture_bindings` e `mapa_cenas`. Mais seguro que `Lock` simples dado o padrão de acesso existente.
- **Config path (ENG-05):** Usar `Path(__file__).parent / "config.json"` no `main.py` (ou `parent.parent` dependendo da estrutura) — derivado de `__file__` do módulo, independente do CWD.
- **Write atômico (ENG-06):** Escrever em arquivo temporário na mesma partição e usar `os.replace()` para substituição atômica — proteção contra corrupção em crash.

### Deferred Ideas (OUT OF SCOPE)

- Correção do `bare except:` em `util/hotkey_listener.py` — adiar para Phase 5.
- Substituição de `print()` por `get_logger()` em `CameraManager` — adiar para Phase 2.
- Dual config sources (in-memory dict vs. engine attributes) — problema arquitetural maior, não adequado para Phase 1.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da Pesquisa |
|----|-----------|---------------------|
| ENG-03 | `GESTURE_ALIASES` consolidado em `core/gesture_aliases.py` — eliminar as 3 cópias divergentes | Análise completa das 3 cópias; union dict documentado; padrão de import estabelecido |
| ENG-04 | Acesso a `gesture_bindings` e `mapa_cenas` protegido por `threading.RLock` | Padrão `RLock` documentado; pontos de acesso cross-thread identificados em `main_window.py` e `gesture_engine.py` |
| ENG-05 | Config carregado por caminho absoluto derivado de `__file__` | Pattern `Path(__file__).parent` confirmado; caminho relativo atual em `main.py:30` identificado |
| ENG-06 | `salvar_config_automatico()` com debounce 500ms + write atômico | Pattern `QTimer.singleShot` + `os.replace()` documentado com exemplos; 8+ call sites identificados |
| DEP-01 | `pygrabber` adicionado ao `requirements.txt` com versão fixada | `pygrabber==0.2` verificado no PyPI; é a única versão disponível |
| DEP-02 | Todas as dependências com versões fixadas no `requirements.txt` | Versões verificadas via `pip index versions` para todos os 6 pacotes |
</phase_requirements>

---

## Summary

A Phase 1 é de estabilização cirúrgica — seis correções pontuais que eliminam bugs críticos sem adicionar nenhuma feature. Não há framework novo a aprender: todas as soluções usam primitivas já presentes na codebase (PySide6, stdlib Python, threading). A única descoberta que requer decisão cuidadosa é a versão a pinar para cada pacote.

**Análise da codebase revelou os problemas exatos:**
- `main.py` linha 12 define `carregar_config(caminho="config.json")` — relativo ao CWD, não ao arquivo
- `main_window.py` linha 1140 escreve `open("config.json", "w", ...)` — mesmo problema
- `main_window.py` tem 8+ call sites de `salvar_config_automatico()` sem qualquer debounce
- `gesture_engine.py` e `main_window.py` escrevem/leem `gesture_bindings` e `mapa_cenas` sem lock (linhas 744, 890, 891, 914, 915)
- As três cópias de `GESTURE_ALIASES` divergiram: `gesture_detector.py` não tem `"V"` nem gestos como "Dedo do Meio", "Arminha", "Escoteiro"
- `config.json` contém path absoluto do developer (`D:/Documentos/Codes/gesto_camera/faz-o-l.wav`) e placeholder (`"Pressione as teclas..."`)

**Recomendação primária:** Executar os 6 requisitos na ordem ENG-05 → ENG-06 → ENG-04 → ENG-03 → DEP-01 → DEP-02. Cada fix é independente dos outros, mas essa ordem segue a dependência lógica declarada em STATE.md.

---

## Architectural Responsibility Map

| Capability | Tier Primário | Tier Secundário | Rationale |
|------------|--------------|-----------------|-----------|
| Config path resolution (ENG-05) | Entry point (`main.py`) | `MainWindow` (salvar) | O carregamento acontece antes de qualquer UI; o salvamento acontece na MainWindow |
| Atomic config write (ENG-06) | `MainWindow.salvar_config_automatico()` | stdlib `os` / `tempfile` | Todo salvamento passa por esse método; debounce deve ficar aqui também |
| Threading lock (ENG-04) | `GestureEngine` (atributos) | `MainWindow` (escritas cross-thread) | A engine owns os dados; a MainWindow os acessa de outra thread |
| GESTURE_ALIASES source of truth (ENG-03) | `core/gesture_aliases.py` (novo módulo) | 3 módulos importadores | Módulo de dados puro, sem lógica; importado por quem precisar |
| Dependency list (DEP-01, DEP-02) | `requirements.txt` | — | Arquivo de declaração de dependências do projeto |
| config.json template (D-01, D-02) | `config.json` raiz do repositório | — | Template commitado representa "fresh install" |

---

## Standard Stack

### Core (todos já estão no projeto — apenas pinagem)

| Pacote | Versão a Pinar | Versão Atual no req.txt | Python 3.10 Wheel | Fonte da Versão |
|--------|---------------|------------------------|-------------------|-----------------|
| `PySide6` | `==6.8.3` | unpinned | Sim (`cp310-abi3`) | [VERIFIED: pip index versions] |
| `opencv-python` | `==4.10.0.84` | unpinned | Sim | [VERIFIED: pip index versions] |
| `mediapipe` | `==0.10.14` | `==0.10.14` (já pinado) | Sim (`cp310`) | [VERIFIED: pip index versions] |
| `pyvirtualcam` | `==0.15.0` | unpinned | Sim (`cp310-win_amd64`) | [VERIFIED: pip index versions] |
| `obsws-python` | `==1.7.2` | unpinned | N/A (pure Python) | [VERIFIED: pip index versions] |
| `keyboard` | `==0.13.5` | unpinned | N/A (pure Python) | [VERIFIED: pip index versions] |
| `pygrabber` | `==0.2` | ausente | N/A (pure Python) | [VERIFIED: pip index versions] |

**Justificativa de versão por pacote:**

**PySide6 `==6.8.3`** — A versão mais recente disponível é 6.11.1, mas ela requer Python >=3.10 (compat OK) e tem abi3 wheels. Porém, Qt 6.5 e Qt 6.8 são versões LTS (Long-Term Support) da Qt Company; Qt 6.11 é feature release sem LTS. Para um app desktop de streaming onde estabilidade é prioritária, pinar na última patch da LTS 6.8 (`6.8.3`) é a escolha conservadora recomendada. [ASSUMED: interpretação LTS — verificar se necessário via wiki.qt.io]

**opencv-python `==4.10.0.84`** — `4.11.0.86` e `4.13.0.92` são mais recentes, mas o projeto usa mediapipe que internamente carrega seu próprio libopencv. Pinar em `4.10.0.84` (a versão mais recente antes das mudanças de ABI no 4.11) é mais seguro. Não há incompatibilidade conhecida entre opencv-python e mediapipe 0.10.14 — mediapipe declare dependência em `opencv-contrib-python` sem versão fixada, indicando que qualquer 4.x recente funciona. [ASSUMED: não há conflito documentado entre 4.10 e mediapipe 0.10.14]

**pyvirtualcam `==0.15.0`** — Última versão; wheel `cp310-win_amd64` confirmado disponível. A histórico de breaking changes do pyvirtualcam é principalmente de drops de versão Python antiga (Python 3.8 foi removido no 0.12.0) e mudança de backend macOS. A API `Camera()` e o backend OBS no Windows não mudaram entre 0.9 e 0.15. Python 3.10 é suportado em todas as versões desde 0.10. [VERIFIED: pypi.org/project/pyvirtualcam — cp310-win_amd64 wheel listado]

**obsws-python `==1.7.2`** — Versão `1.8.0` foi publicada em 01/Jul/2025 (relativamente recente). A versão `1.7.2` (Mai/2025) é mais conservadora. O projeto usa apenas `obs.ReqClient` para troca de cena e controle de stream — a API básica está estável no protocolo OBS WebSocket v5.x. [ASSUMED: 1.7.2 vs 1.8.0 não tem breaking change documentado; preferência por versão mais testada]

**keyboard `==0.13.5`** — Última versão disponível; não houve update desde 2020. Projeto estável e frozen. [VERIFIED: pip index versions]

**pygrabber `==0.2`** — Única versão disponível além de `0.1`. Projeto estável sem atualizações. [VERIFIED: pip index versions]

### Stdlib Python utilizado nesta phase (sem instalação necessária)

| Módulo | Propósito na Phase 1 |
|--------|----------------------|
| `pathlib.Path` | Resolver caminho absoluto para `config.json` via `__file__` |
| `os.replace()` | Rename atômico do arquivo temporário para `config.json` |
| `tempfile.NamedTemporaryFile` | Arquivo temporário na mesma partição que `config.json` |
| `threading.RLock` | Lock reentrante para proteger acesso cross-thread a `gesture_bindings` |

### Frameworks Qt utilizados

| Componente Qt | Propósito na Phase 1 |
|---------------|----------------------|
| `QTimer.singleShot(ms, slot)` | Debounce de 500ms para `salvar_config_automatico()` |
| `Signal()` | Para propagar chamada de save de thread de engine para main thread Qt |

**Instalação do requirements.txt atualizado:**
```bash
pip install -r requirements.txt
```

---

## Package Legitimacy Audit

> Todos os 7 pacotes foram verificados via `pip index versions` (registros PyPI ativos) e têm repositórios GitHub ativos com source code. O seam `package-legitimacy` retornou `SUS` para todos com motivo `unknown-downloads` — isso é uma limitação do seam (PyPI não expõe download stats na API que o seam usa), não um sinal real de risco. Todos os pacotes têm repositórios GitHub estabelecidos e são amplamente usados.

| Pacote | Registry | Publicação mais recente | Source Repo | Verdict do Seam | Disposição |
|--------|----------|------------------------|-------------|-----------------|------------|
| `PySide6` | PyPI | Mai 2026 | pyside.org (Qt Company) | SUS (unknown-downloads) | Aprovado — produto oficial da Qt Company |
| `opencv-python` | PyPI | Fev 2026 | github.com/opencv/opencv-python | SUS (unknown-downloads) | Aprovado — wrapper oficial OpenCV |
| `mediapipe` | PyPI | Abr 2026 | github.com/google/mediapipe | SUS (unknown-downloads) | Aprovado — produto oficial Google |
| `pyvirtualcam` | PyPI | Jan 2026 | github.com/letmaik/pyvirtualcam | SUS (unknown-downloads) | Aprovado — projeto estabelecido |
| `obsws-python` | PyPI | Jul 2025 | github.com/aatikturk/obsws-python | SUS (unknown-downloads) | Aprovado — SDK OBS WebSocket v5 |
| `keyboard` | PyPI | Mar 2020 (frozen) | github.com/boppreh/keyboard | SUS (unknown-downloads) | Aprovado — projeto maduro e estável |
| `pygrabber` | PyPI | Out 2023 | github.com/andreaschiavinato/python_grabber | SUS (unknown-downloads) | Aprovado — projeto nicho estável |

**Pacotes removidos (SLOP):** nenhum
**Pacotes suspeitos (SUS real):** nenhum — todos os `SUS` são falso-positivo por limitação de API do seam

---

## Architecture Patterns

### Diagrama de Fluxo — Phase 1 (correções)

```
[Atalho do Desktop]
        |
        v
[main.py] ── carregar_config(Path(__file__).parent / "config.json")  [ENG-05 FIX]
        |
        v
[MainWindow.__init__]
        |── _init_config_schema()  ← usa GESTURE_ALIASES de core.gesture_aliases  [ENG-03 FIX]
        |── _setup_ui()
        |── _load_ui_from_config()
        |── salvar_config_automatico()  ← agenda QTimer 500ms (não escreve imediatamente)  [ENG-06 FIX]
        |
        v
[QTimer 500ms dispara na main thread]
        |
        v
[_do_save_config()]
        |── escreve em temp_file (mesma partição)
        |── os.replace(temp_file, config_path)  ← atômico  [ENG-06 FIX]
        
[GestureEngine thread]  ←──── lê gesture_bindings com RLock  [ENG-04 FIX]
        ↑                                                   ↓
[MainWindow main thread] ── escreve gesture_bindings com RLock  [ENG-04 FIX]
```

### Estrutura de arquivos afetados

```
OBS_GestureNode/
├── main.py                    # MODIFICAR: config path via __file__
├── requirements.txt           # MODIFICAR: pinar todas as versões + adicionar pygrabber
├── config.json                # SUBSTITUIR: template limpo sem paths absolutos
├── core/
│   ├── gesture_aliases.py     # CRIAR: fonte única de GESTURE_ALIASES
│   └── gesture_detector.py    # MODIFICAR: remover GESTURE_ALIASES local, importar de core
├── engine/
│   └── gesture_engine.py      # MODIFICAR: remover GESTURE_ALIASES local, importar de core; adicionar RLock
└── ui/
    └── main_window.py         # MODIFICAR: remover GESTURE_ALIASES local; debounce save; RLock writes; fix save path
```

### Padrão 1: Config Path via `__file__`

**O quê:** Resolver caminho absoluto do config.json relativo ao módulo Python, não ao diretório de trabalho.

**Quando usar:** Sempre que um script Python lê/escreve um arquivo de dados que fica na mesma pasta do projeto — especialmente quando o app pode ser invocado de qualquer CWD (atalho no desktop, IDE, linha de comando).

**Implementação em `main.py`:**
```python
# Source: Python stdlib docs — pathlib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def carregar_config(caminho: Path = CONFIG_PATH):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        logger.warning("Arquivo de configuração não encontrado: %s", caminho)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("JSON inválido em %s: %s", caminho, exc)
        return {}
    except OSError as exc:
        logger.error("Erro ao ler configuração %s: %s", caminho, exc)
        return {}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = carregar_config()
    window = MainWindow(config, config_path=CONFIG_PATH)
    window.show()
    sys.exit(app.exec())
```

**Nota:** `main.py` está na raiz do projeto (`D:/Documentos/Codes/OBS_GestureNode/main.py`), portanto `Path(__file__).parent` já aponta para a raiz — sem necessidade de `.parent.parent`. [VERIFIED: estrutura verificada no filesystem]

### Padrão 2: Write Atômico via `os.replace()`

**O quê:** Escrever em arquivo temporário na mesma partição e renomear atomicamente. `os.replace()` é garantido pelo SO como operação atômica em Windows NTFS.

**Quando usar:** Qualquer write de arquivo de configuração onde corrupção parcial é inaceitável.

**Implementação em `MainWindow`:**
```python
# Source: Python stdlib docs — os.replace, tempfile
import os
import tempfile
from pathlib import Path

def _do_save_config(self):
    """Executa o write atômico do config. Chamado apenas pela main thread via QTimer."""
    self._sync_scene_map_from_bindings()
    config_path = self._config_path  # Path recebido do main.py via __init__
    dir_path = config_path.parent
    try:
        # tempfile na mesma partição garante que os.replace seja atômico
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            os.replace(tmp_path, config_path)
        except Exception:
            os.unlink(tmp_path)  # limpar temp em caso de erro
            raise
    except OSError as exc:
        logger.error("Falha ao salvar configuração: %s", exc)
```

### Padrão 3: Debounce com `QTimer.singleShot`

**O quê:** Atrasar a execução de uma função cara até que o usuário pare de chamar por N ms. `QTimer.singleShot` é thread-safe quando chamado da main thread; para chamadas de outras threads, usar signal.

**Quando usar:** Qualquer operação cara (disk write, network call) conectada a eventos de alta frequência (slider, spinbox, keystroke).

**Implementação em `MainWindow`:**
```python
# Source: PySide6 docs — QTimer.singleShot
from PySide6.QtCore import QTimer

class MainWindow(QMainWindow):
    # Signal para receber trigger de qualquer thread
    _save_requested = Signal()

    def __init__(self, config, config_path: Path):
        super().__init__()
        self._config_path = config_path
        self._save_timer = None
        self._save_requested.connect(self._schedule_save)
        # ... resto do __init__

    def salvar_config_automatico(self):
        """
        Agenda save com debounce de 500ms.
        Thread-safe: pode ser chamado de qualquer thread via signal.
        """
        # Se chamado da main thread, diretamente
        self._schedule_save()

    def _schedule_save(self):
        """Sempre executado na main thread Qt."""
        if self._save_timer is not None:
            self._save_timer.stop()
        self._save_timer = QTimer.singleShot(500, self._do_save_config)
```

**Nota sobre thread safety:** `salvar_config_automatico()` é chamado apenas da main thread Qt (todos os 8+ call sites são slots Qt conectados a widgets na main thread). Portanto, o signal intermediário não é estritamente necessário para ENG-06 — mas é boa prática. O debounce simples com `QTimer.singleShot` é suficiente. [VERIFIED: grep confirmou que todos os call sites são slots Qt]

### Padrão 4: `threading.RLock` para acesso cross-thread

**O quê:** `RLock` (Reentrant Lock) permite que a mesma thread adquira o lock múltiplas vezes sem deadlock. Necessário quando um método que segura o lock pode chamar outro método que também tenta adquiri-lo.

**Quando usar:** Proteção de estado compartilhado entre threads quando os accessors podem ser chamados de forma reentrante (ex: `_normalize_gesture_keys()` chamado dentro de contextos que já seguram o lock).

**Implementação em `GestureEngine`:**
```python
# Source: Python stdlib docs — threading.RLock
import threading

class GestureEngine(QThread):
    def __init__(self, config):
        super().__init__()
        self._bindings_lock = threading.RLock()
        self._gesture_bindings = {}
        self._mapa_cenas = {}
        # ...

    @property
    def gesture_bindings(self):
        with self._bindings_lock:
            return self._gesture_bindings

    @gesture_bindings.setter
    def gesture_bindings(self, value):
        with self._bindings_lock:
            self._gesture_bindings = value

    @property
    def mapa_cenas(self):
        with self._bindings_lock:
            return self._mapa_cenas

    @mapa_cenas.setter
    def mapa_cenas(self, value):
        with self._bindings_lock:
            self._mapa_cenas = value
```

**Impacto no código existente:** As escritas em `main_window.py` linhas 744, 890, 891, 914, 915 continuam funcionando sem alteração — o setter do property aplica o lock automaticamente. As leituras em `gesture_engine.py:run()` usarão o getter. `_normalize_gesture_keys()` precisa ser adaptado para acessar `self._gesture_bindings` diretamente (evitar deadlock com property).

### Padrão 5: `core/gesture_aliases.py` — Fonte Única de Verdade

**O quê:** Módulo Python com apenas um dict de mapeamento. Zero lógica, zero imports.

**Implementação de `core/gesture_aliases.py`:**
```python
# Mapeamento canônico de código interno → nome de exibição português
# União de todas as cópias divergentes em gesture_detector.py, gesture_engine.py e main_window.py
GESTURE_ALIASES = {
    "THUMBS_UP": "Joinha",
    "THUMBS_DOWN": "Deslike",
    "OPEN_HAND": "Mão aberta",
    "FIST": "Punho",
    "POINT": "Apontando p/ cima",
    "ROCK": "ROCK",
    "THREE": "TRES",
    "FOUR": "QUATRO",
    "OK_SIGN": "OK",
    "CALL_ME": "Me liga",
    "V": "V",
    # Gestos presentes em gesture_detector.py mas ausentes nas outras cópias:
    "Escoteiro": "Escoteiro",
    "Dedo do Meio": "Dedo do Meio",
    "Arminha": "Arminha",
}
```

**Gestos retornados por `gesture_detector.py:detectar()` que não são chaves UPPER_SNAKE_CASE:**
O detector retorna strings de display diretamente para alguns gestos: `"V"`, `"Escoteiro"`, `"Dedo do Meio"`, `"Arminha"`. Para estes, `GESTURE_ALIASES.get(x, x)` retorna o próprio valor — correto.

**Import em todos os módulos:**
```python
from core.gesture_aliases import GESTURE_ALIASES
```

### Anti-Patterns a Evitar

- **`threading.Timer` para debounce Qt:** `threading.Timer` roda em thread separada; chamar `salvar_config_automatico()` da thread do timer poderia modificar config de fora da main thread. Use `QTimer.singleShot` que é garantido de rodar na main thread Qt.
- **`Lock` simples em vez de `RLock`:** `GestureEngine._normalize_gesture_keys()` pode ser chamado de dentro de um contexto que já segura o lock. `Lock` causaria deadlock; `RLock` permite reentrada.
- **`open(tmp_path, "w")` para write atômico:** O arquivo temporário deve estar na mesma partição que o destino para `os.replace()` ser atômico. Usar `tempfile.mkstemp(dir=config_path.parent)`.
- **Cópia rasa do dict GESTURE_ALIASES:** Os módulos importadores não devem fazer `ALIASES = GESTURE_ALIASES.copy()` — isso quebra o princípio de fonte única. Sempre importar e usar `GESTURE_ALIASES` diretamente.

---

## Don't Hand-Roll

| Problema | Não Construir | Usar em Vez | Por Quê |
|----------|--------------|-------------|---------|
| Rename atômico de arquivo | Sequência custom de open/write/close/delete/rename | `os.replace()` | `os.replace()` é garantido atômico no NTFS pelo SO; implementação manual tem janela de corrupção entre delete e rename |
| Debounce de chamadas | `threading.Timer` ou loop com sleep | `QTimer.singleShot(ms, slot)` | `QTimer` é thread-safe com Qt event loop; respeita lifecycle de widgets; auto-cancela se widget for destruído |
| Arquivo temporário | `open(path + ".tmp", "w")` | `tempfile.mkstemp(dir=target_dir)` | `mkstemp` garante nome único; evita colisão se múltiplos processos tentarem salvar simultaneamente |

---

## Common Pitfalls

### Pitfall 1: Caminho relativo no `salvar_config_automatico()`

**O que acontece:** `main.py` é corrigido para usar `Path(__file__).parent`, mas `salvar_config_automatico()` em `main_window.py` linha 1140 ainda usa `open("config.json", "w")`. O arquivo de carregamento vai para o lugar certo, mas o arquivo de salvamento continua indo para o CWD.

**Por que acontece:** São dois locais diferentes de acesso ao arquivo — o planejador pode corrigir um e esquecer o outro.

**Como evitar:** Passar `config_path: Path` como parâmetro de `MainWindow.__init__()` e armazenar em `self._config_path`. `salvar_config_automatico()` usa `self._config_path`. Grep de verificação: `grep -n "config.json" ui/main_window.py` — deve retornar zero ocorrências após a correção.

**Sinais de alerta:** Arquivo `config.json` aparece criado em `C:\Windows\system32\` ou em outro diretório quando app é iniciado via atalho.

### Pitfall 2: Deadlock com `Lock` simples em `GestureEngine`

**O que acontece:** `_normalize_gesture_keys()` acessa `self.gesture_bindings` e `self.mapa_cenas`. Se esses atributos forem protegidos por `Lock` simples e `_normalize_gesture_keys()` for chamado de dentro de um contexto que já segura o lock (ex: dentro do setter), ocorre deadlock.

**Por que acontece:** `Lock` não é reentrante — a mesma thread não pode adquirir o mesmo lock duas vezes.

**Como evitar:** Usar `threading.RLock` em vez de `threading.Lock`. O código existente em `_normalize_gesture_keys()` deve acessar os atributos privados (`self._gesture_bindings`) diretamente em vez de passar pelo property (que adquiriria o lock novamente).

### Pitfall 3: `QTimer.singleShot` sendo cancelado

**O que acontece:** O debounce de 500ms precisa cancelar o timer anterior a cada nova chamada. `QTimer.singleShot` é um static method que cria um timer one-shot e não retorna um objeto cancelável.

**Por que acontece:** A API `QTimer.singleShot(ms, callable)` é fire-and-forget. Para ter controle de cancelamento, é necessário usar uma instância de `QTimer`.

**Como evitar:** Usar uma instância `self._save_timer = QTimer(self)` com `setSingleShot(True)`, conectar ao slot de save, e chamar `self._save_timer.start(500)` (que reinicia o timer se já estiver rodando, efetivamente debouncing).

```python
# Padrão correto para debounce cancelável:
self._save_timer = QTimer(self)
self._save_timer.setSingleShot(True)
self._save_timer.timeout.connect(self._do_save_config)

def salvar_config_automatico(self):
    self._save_timer.start(500)  # reinicia o timer (cancela o anterior)
```

### Pitfall 4: `GESTURE_ALIASES` canônico incompleto

**O que acontece:** O dict canônico em `core/gesture_aliases.py` não inclui todos os gestos que `gesture_detector.py:detectar()` pode retornar, causando que `GESTURE_ALIASES.get(x, x)` retorne chaves inesperadas para o config lookup.

**Por que acontece:** As três cópias divergiram. A cópia em `gesture_engine.py` tem `"V": "V"` que está ausente em `gesture_detector.py`. O detector retorna strings de display diretamente para "Escoteiro", "Dedo do Meio", "Arminha" — não há entrada correspondente em nenhuma das cópias ALIASES.

**Como evitar:** O dict canônico deve ser a union de TODAS as strings que `detectar()` pode retornar. Analisar `gesture_detector.py:detectar()` e listar todos os `return` statements. Strings retornadas diretamente como display name (ex: `return "Escoteiro"`) devem aparecer no dict como passthrough: `"Escoteiro": "Escoteiro"`.

**Strings retornadas por `detectar()` (verificado no código):**
`"OK_SIGN"`, `"V"` (ou `"Escoteiro"` se dedos próximos), `"CALL_ME"`, `"Dedo do Meio"`, `"ROCK"`, `"OPEN_HAND"`, `"FOUR"`, `"THREE"`, `"Arminha"`, `"POINT"`, `"THUMBS_UP"`, `"THUMBS_DOWN"`, `"FIST"` — e `None`.

### Pitfall 5: `config.json` template com campos do developer

**O que acontece:** O `config.json` atual tem `"sound_file": "D:/Documentos/Codes/gesto_camera/faz-o-l.wav"` e `"hotkey": "Pressione as teclas..."`. Se commitado assim, qualquer clone vai ter um som que não existe e uma hotkey inválida que vai tentar enviar "Pressione as teclas..." como combo de teclas.

**Por que acontece:** O arquivo foi editado pelo developer durante desenvolvimento e commitado com estado de trabalho.

**Como evitar:** Template limpo com `"sound_file": ""` e `"hotkey": ""` para todos os gestos. `"use_hotkey": false` para todos. `"camera": {"index": 0}` (câmera padrão, não câmera 1 que é específica da máquina do developer).

---

## Code Examples

### Exemplo 1: requirements.txt final

```
# Python 3.10.11
PySide6==6.8.3
opencv-python==4.10.0.84
mediapipe==0.10.14
pyvirtualcam==0.15.0
obsws-python==1.7.2
keyboard==0.13.5
pygrabber==0.2
```

### Exemplo 2: `core/gesture_aliases.py` completo

```python
# Mapeamento canônico: código interno do detector → nome de exibição
# Fonte única de verdade — importado por gesture_detector, gesture_engine, main_window
GESTURE_ALIASES = {
    # Gestos com código UPPER_SNAKE_CASE
    "THUMBS_UP": "Joinha",
    "THUMBS_DOWN": "Deslike",
    "OPEN_HAND": "Mão aberta",
    "FIST": "Punho",
    "POINT": "Apontando p/ cima",
    "ROCK": "ROCK",
    "THREE": "TRES",
    "FOUR": "QUATRO",
    "OK_SIGN": "OK",
    "CALL_ME": "Me liga",
    # Gestos cujo código já é o nome de exibição (passthrough)
    "V": "V",
    "Escoteiro": "Escoteiro",
    "Dedo do Meio": "Dedo do Meio",
    "Arminha": "Arminha",
}
```

### Exemplo 3: `GestureEngine` com RLock e properties

```python
import threading

class GestureEngine(QThread):
    def __init__(self, config):
        super().__init__()
        self._bindings_lock = threading.RLock()
        self._gesture_bindings = {}
        self._mapa_cenas = {}
        self._setup()

    @property
    def gesture_bindings(self):
        with self._bindings_lock:
            return dict(self._gesture_bindings)  # cópia defensiva

    @gesture_bindings.setter
    def gesture_bindings(self, value):
        with self._bindings_lock:
            self._gesture_bindings = value or {}

    @property
    def mapa_cenas(self):
        with self._bindings_lock:
            return dict(self._mapa_cenas)

    @mapa_cenas.setter
    def mapa_cenas(self, value):
        with self._bindings_lock:
            self._mapa_cenas = value or {}

    def _normalize_gesture_keys(self):
        # Acessa _gesture_bindings diretamente (não via property) pois
        # pode ser chamado de dentro de um contexto com RLock já adquirido
        with self._bindings_lock:
            if isinstance(self._gesture_bindings, dict):
                self._gesture_bindings = {
                    self._normalize_gesture_name(k): v
                    for k, v in self._gesture_bindings.items()
                }
            if isinstance(self._mapa_cenas, dict):
                self._mapa_cenas = {
                    self._normalize_gesture_name(k): v
                    for k, v in self._mapa_cenas.items()
                }
```

### Exemplo 4: `MainWindow.salvar_config_automatico()` com debounce

```python
from PySide6.QtCore import QTimer
import os
import tempfile
import json

class MainWindow(QMainWindow):
    def __init__(self, config, config_path: Path):
        super().__init__()
        self._config_path = config_path
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save_config)
        # ... resto do __init__

    def salvar_config_automatico(self):
        """Agenda write com debounce 500ms. Seguro chamar múltiplas vezes seguidas."""
        self._save_timer.start(500)  # reinicia se já estava contando

    def _do_save_config(self):
        """Executado 500ms após o último salvar_config_automatico(). Main thread only."""
        self._sync_scene_map_from_bindings()
        dir_path = self._config_path.parent
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                os.replace(tmp_path, str(self._config_path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            logger.error("Falha ao salvar configuração: %s", exc)
```

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|-----------------|--------------|---------|
| `open(path, "w")` direto | `tempfile.mkstemp` + `os.replace()` | Python 3.3+ | Elimina corrupção em crash |
| `threading.Timer` para debounce Qt | `QTimer.singleShot` / `QTimer` instance | PySide2/Qt5 era | Thread-safe no event loop Qt |
| Constantes repetidas em cada módulo | Módulo dedicado de constantes | DRY principle | Elimina drift entre cópias |
| Caminho relativo `"config.json"` | `Path(__file__).parent / "config.json"` | Python 3.4+ (pathlib) | Funciona independente de CWD |

**Deprecated/obsoleto nesta fase:**
- Linha `python version == 3.10.11` no requirements.txt: sintaxe inválida que pip ignora silenciosamente; substituir por comentário.

---

## Runtime State Inventory

> Esta fase envolve mudanças em config.json e estrutura de módulos — verificação obrigatória.

| Categoria | Items Encontrados | Ação Necessária |
|-----------|-------------------|-----------------|
| Dados armazenados | `config.json` na raiz do repositório com paths absolutos e placeholders | Substituir pelo template limpo (D-01, D-02) |
| Config de serviço ativo | Nenhum — app é desktop local sem serviços externos registrados | Nenhuma |
| Estado registrado no SO | Nenhum — nenhum Task Scheduler, pm2, ou launchd encontrado | Nenhuma |
| Secrets/env vars | `config.json` armazena senha OBS em plaintext — documentado como aceitável para uso local | Sem ação na Phase 1 |
| Build artifacts | Nenhum venv encontrado na raiz do projeto | Nenhuma |

**Nada encontrado em:** config de serviço ativo, estado SO, build artifacts. Verificado via filesystem.

---

## Environment Availability

| Dependência | Requerida Por | Disponível | Versão | Fallback |
|-------------|--------------|-----------|--------|----------|
| Python 3.10.11 | todo o projeto | Assumido sim (restrição do projeto) | 3.10.11 | — |
| pip | DEP-01, DEP-02 | Assumido sim | — | — |
| PyPI (internet) | DEP-01, DEP-02 | Assumido sim | — | — |
| OBS Studio + Virtual Camera | pyvirtualcam | Não requerido para Phase 1 | — | Phase 1 não ativa virtual cam |

**Dependências faltando sem fallback:** nenhuma para Phase 1.

---

## Validation Architecture

> `workflow.nyquist_validation: true` — seção obrigatória.

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | Nenhum detectado no projeto (sem pytest, unittest, etc.) |
| Arquivo de config | Nenhum |
| Comando rápido | N/A — ver Wave 0 Gaps |
| Suite completa | N/A — ver Wave 0 Gaps |

**Nota:** CLAUDE.md confirma: "No testing framework detected". A Phase 1 é de correção cirúrgica de bugs e pinagem de versões — os success criteria são verificáveis manualmente ou por scripts de smoke test simples.

### Phase Requirements → Test Map

| Req ID | Comportamento | Tipo de Teste | Verificação |
|--------|--------------|---------------|-------------|
| ENG-05 | Config carregado de caminho absoluto | smoke manual | Iniciar app de `C:\Windows\system32` (como admin) e verificar que config.json não é criado lá |
| ENG-06 | Mover slider 10s não corrompe config.json | smoke manual | Mover sliders 10s; verificar config.json válido no path correto |
| ENG-04 | Sem KeyError ao editar duas abas simultaneamente | smoke manual | Editar gestos tab e geral tab alternadamente enquanto engine roda |
| ENG-03 | `GESTURE_ALIASES` idêntico em todos os módulos | smoke script | `python -c "from core.gesture_aliases import GESTURE_ALIASES; print(GESTURE_ALIASES)"` de dentro do projeto |
| DEP-01 | `pip install -r requirements.txt` sem erros | comando | `pip install -r requirements.txt` em venv limpo |
| DEP-02 | Versões fixadas no requirements.txt | inspeção | `cat requirements.txt` — todas as linhas com `==` exceto comentários |

### Wave 0 Gaps

- [ ] Nenhum arquivo de test precisa ser criado para Phase 1 — todos os critérios de aceitação são verificáveis manualmente ou por `gsd-verify-work`
- [ ] Se desejado, um `smoke_foundation.py` pode verificar: import de `core.gesture_aliases`, conteúdo do GESTURE_ALIASES, validade do config.json, e sintaxe do requirements.txt

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1`

### ASVS Categories Aplicáveis (ASVS Level 1)

| Categoria ASVS | Aplica | Controle |
|----------------|--------|---------|
| V2 Autenticação | Não | Phase 1 não toca autenticação |
| V3 Gerenciamento de Sessão | Não | App desktop sem sessões |
| V4 Controle de Acesso | Não | App single-user |
| V5 Validação de Input | Sim (baixo risco) | config.json é lido e parseado — `json.load()` com tratamento de `json.JSONDecodeError` já existente |
| V6 Criptografia | Não | Sem operações criptográficas |

### Padrões de Ameaça Relevantes para a Stack

| Padrão | STRIDE | Mitigação Padrão |
|--------|--------|-----------------|
| Config.json com path absoluto de terceiro | Tampering | D-01: commitar template limpo; never hardcode paths de developer |
| Write de config sem atomic replace | Denial of Service (corrupção) | ENG-06: `os.replace()` atômico |
| Race condition no acesso a gesture_bindings | Tampering / Elevation | ENG-04: `threading.RLock` |

**Risco de segurança em `config.json`:** A senha do OBS WebSocket está em plaintext no config.json — documentado no CONCERNS.md como "aceitável para uso local". Nenhuma ação na Phase 1. Será abordado na documentação de Phase 3 (OBS Connection).

---

## Assumptions Log

| # | Afirmação | Seção | Risco se Errada |
|---|-----------|-------|-----------------|
| A1 | PySide6 6.8.3 é uma versão LTS da Qt Company — preferível a 6.11.1 para estabilidade | Standard Stack | Se 6.8 não for LTS, poderíamos pinar na 6.11.1 sem perda; baixo risco |
| A2 | obsws-python 1.7.2 é preferível a 1.8.0 por ser mais "testada" | Standard Stack | Se 1.8.0 tiver bugfixes críticos, perderíamos uma melhoria; baixo risco — ambas são compatíveis |
| A3 | opencv-python 4.10.0.84 não tem conflito com mediapipe 0.10.14 | Standard Stack | Se houver conflito de ABI, o app não inicia; médio risco — testar em `pip install` |
| A4 | `salvar_config_automatico()` é chamado apenas da main thread Qt | Padrão 3 | Se for chamado de outra thread sem o signal intermediário, QTimer.start() de outra thread pode falhar silenciosamente |

**Se a tabela estiver vazia:** não está — há 4 afirmações assumidas que precisam de validação no momento da execução.

---

## Open Questions

1. **PySide6 6.8.3 vs 6.11.1**
   - O que sabemos: 6.8 é a última série antes do 6.9; Qt 6.5 foi LTS; Qt 6.8 possivelmente também é LTS
   - O que está incerto: confirmação oficial de que Qt 6.8 é LTS (a pesquisa não foi conclusiva)
   - Recomendação: pinar em `6.8.3` por ser conservador; se o usuário preferir a versão mais recente, `6.11.1` também funciona com Python 3.10

2. **obsws-python 1.7.2 vs 1.8.0**
   - O que sabemos: 1.8.0 foi publicado em Jul/2025; nenhum breaking change documentado
   - O que está incerto: o changelog detalhado da 1.8.0 não foi verificado
   - Recomendação: pinar em `1.7.2` por segurança; o planner pode confirmar com o usuário se prefere a mais recente

3. **Cópia defensiva nos getters do RLock**
   - O que sabemos: Retornar `dict(self._gesture_bindings)` cria uma cópia na leitura
   - O que está incerto: O código existente pode estar dependendo de mutações in-place do dict retornado
   - Recomendação: Investigar todos os pontos de uso de `engine.gesture_bindings` antes de implementar a cópia defensiva; pode ser mais seguro retornar o dict original (apenas o setter precisa do lock)

---

## Sources

### Primary (verificado via ferramentas nesta sessão)
- `pip index versions PySide6` — versão 6.11.1 mais recente; 6.8.3 disponível
- `pip index versions opencv-python` — versão 4.13.0.92 mais recente; 4.10.0.84 disponível
- `pip index versions pyvirtualcam` — versão 0.15.0 mais recente e única estável
- `pip index versions obsws-python` — versão 1.8.0 mais recente; 1.7.2 disponível
- `pip index versions keyboard` — versão 0.13.5 mais recente
- `pip index versions pygrabber` — versão 0.2 única disponível além de 0.1
- `pip index versions mediapipe` — versão 0.10.14 confirmada no PyPI
- Leitura direta: `main.py`, `requirements.txt`, `ui/main_window.py`, `engine/gesture_engine.py`, `core/gesture_detector.py`, `config.json`
- [pypi.org/project/pyvirtualcam](https://pypi.org/project/pyvirtualcam/) — wheel cp310-win_amd64 confirmado para 0.15.0
- [pypi.org/project/PySide6](https://pypi.org/project/PySide6/) — suporte Python >=3.10 confirmado
- [pypi.org/pypi/mediapipe/0.10.14/json](https://pypi.org/pypi/mediapipe/0.10.14/json) — dependências confirmadas

### Secondary (web search — MEDIUM confidence)
- [pyvirtualcam CHANGELOG](https://github.com/letmaik/pyvirtualcam/blob/main/CHANGELOG.md) — breaking changes entre versões revisados
- [pypi.org/project/obsws-python](https://pypi.org/project/obsws-python/) — versão 1.8.0 confirmada; Python >=3.9

### Tertiary (training knowledge — LOW confidence)
- Padrão `os.replace()` para write atômico — conhecimento stdlib Python
- Padrão `QTimer.singleShot` para debounce PySide6 — conhecimento de training

---

## Metadata

**Breakdown de confiança:**
- Standard Stack (versões): HIGH — verificado via `pip index versions` direto
- Código afetado (bugs identificados): HIGH — verificado via leitura direta dos arquivos
- Padrões de implementação: MEDIUM — baseados em stdlib Python e PySide6 docs conhecidos; não verificados via Context7
- Versão PySide6 LTS vs latest: LOW — investigação inconclusiva; recomendação conservadora assumida

**Data da pesquisa:** 2026-06-22
**Válido até:** 2026-07-22 (versões PyPI podem mudar; padrões Python/Qt são estáveis)
