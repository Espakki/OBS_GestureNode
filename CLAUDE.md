# CLAUDE.md

App desktop Windows (PySide6) que controla o OBS Studio por gestos de mão via webcam.
MediaPipe para detecção, PyAV para captura, `obsws-python` para o OBS. A interface é
**Qt Quick (QML) hospedado dentro de uma casca de Widgets** — uma aba por `QQuickWidget`.

## Comece por aqui

1. **`.planning/STATE.md`** — onde o projeto está. É o único arquivo que diz status.
2. **`.planning/DECISIONS.md`** — leia antes de chamar qualquer coisa de bug. Várias
   escolhas parecem inconsistência até você ver o motivo registrado.
3. **`.planning/PITFALLS.md`** — antes de encostar em câmera, MediaPipe ou VCam.
4. **`.planning/BACKLOG.md`** — o que está aberto e por quê.

Se o repo esteve parado, **rode `git pull` antes de analisar qualquer coisa.** Já houve um
caso do checkout local estar 4 meses atrás do remoto, e toda a análise saiu errada.

## Stack

Não existe `pyproject.toml`, `setup.cfg`, `.python-version` nem lockfile. O manifesto
inteiro são dois arquivos.

| | Versão | Onde está declarado |
|---|---|---|
| Python | **3.10.11** | comentário na 1ª linha de `requirements.txt` |
| PySide6 | **6.8.3** (Qt 6.8.3) | `requirements.txt` |
| pytest | 9.1.1 | `requirements-dev.txt` |
| PyInstaller | 6.22.2 | `requirements-dev.txt` |
| mediapipe | 0.10.14 — pin rígido, ver D-04 | `requirements.txt` |
| av (PyAV) | 14.2.0 — última wheel cp310/win_amd64 | `requirements.txt` |

### Comandos reais

Rodar o app:

```powershell
.venv\Scripts\python.exe main.py
```

Rodar a casca remodelada — rail vertical no lugar das abas (D-52):

```powershell
$env:GESTURENODE_UI='novo'; .venv\Scripts\python.exe main.py
```

Rodar caindo para a interface antiga de Widgets (saída de emergência do D-49):

```powershell
$env:GESTURENODE_UI='widgets'; .venv\Scripts\python.exe main.py
```

Testes — **251 testes, ~4 s, sem webcam e sem OBS**:

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

Build (gera `dist/main/`, ~480 MB; distribua a **pasta inteira**):

```powershell
.venv\Scripts\python.exe -m PyInstaller main.spec
```

### Lint e format: **não existem**

Sem ruff, black, flake8, pylint, mypy, isort — nem instalados, nem configurados. Sem
`.pre-commit-config.yaml`. Sem `.github/`, ou seja, **sem CI**: o que você não rodou
localmente não foi verificado por ninguém.

Não introduza um formatador sem pedir. Muitos módulos aqui têm docstring longa que é o
registro do *porquê* da escolha; uma reformatação em massa suja o `git blame` que dá acesso
a esse registro, e o ganho é zero num projeto de um desenvolvedor.

## Estrutura

```
main.py                  entrypoint: QQuickStyle.setStyle("Basic") ANTES do QApplication
version.py               versão, nome do app e repositório — bump manual (D-51)
main.spec                PyInstaller; empacota ui/qml como data
core/                    domínio, sem Qt em estado_app.py (D-47)
engine/gesture_engine.py QThread com o loop principal
integrations/            OBS (controller + thread de conexão)
actions/                 despacho de ação por tipo
plataforma/              tudo que depende de SO fica atrás desta fronteira (D-42)
util/                    logger, caminhos
ui/
  main_window.py         janela; monta as abas e conecta os contratos
  mixins/                comportamento da janela, fatiado por assunto
  tabs/                  geral_tab.py (Widgets)  +  geral_tab_qml.py (QML), mesmo contrato
  tabs/geral_contrato.py o contrato: sinais de intenção + métodos. Não expõe widget.
  qml/                   15 .qml + qmldir + as pontes .py, no MESMO diretório
  qml/novo/              a casca remodelada: módulo QML próprio (`module novo`)
  shell_novo.py          hospeda novo/App.qml e cumpre os contratos que os mixins esperam
tests/                   pytest, automatizado, sem hardware
teste/                   scripts MANUAIS antigos, exigem webcam e OBS. Não é o pytest.
```

**Não há `.qrc`.** Nenhum recurso compilado, nenhum `*_rc.py`, nenhum `pyside6-rcc`. Os
`.qml` são lidos do disco em runtime com `QUrl.fromLocalFile`. Duas consequências que
custam caro se esquecidas:

- O diretório precisa entrar no import path (`self.engine().addImportPath(...)`), senão o
  `qmldir` não é achado e o singleton `Tema` não resolve.
- `main.spec` precisa de `('ui/qml', 'ui/qml')` em `datas`, senão o app empacotado não
  acha a interface e cai para Widgets. Se você criar um `.qml` novo, ele já entra junto
  (a pasta inteira é copiada) — mas se mover a pasta, atualize o spec.

## Como o Python chega ao QML

**Só `setContextProperty`.** Não há `@QmlElement`, `QML_IMPORT_NAME`, `qmlRegisterType` nem
`qmlRegisterSingletonType` em lugar nenhum do repositório. Não introduza um sem decisão
nova — hoje as quatro abas seguem o mesmo desenho, e misturar os dois mecanismos custa a
única coisa boa que ele tem, que é ser previsível.

Também **não há `QQmlApplicationEngine`**: a casca é `QMainWindow`/`QTabWidget`, e cada aba
é um `QQuickWidget`. Foi assim que a migração pôde ser incremental (D-49).

| Objeto de contexto | Classe da ponte | Widget hospedeiro |
|---|---|---|
| `ponte` | `PonteGeral` | `ui/tabs/geral_tab_qml.py:62` |
| `ponteGestos` | `PonteGestos` | `ui/tabs/gestos_tab_qml.py:48` |
| `ponteObs` | `PonteObs` | `ui/tabs/obs_tab_qml.py:42` |
| `ponteSobre` | `PonteSobre` | `ui/tabs/sobre_tab_qml.py:30` |

A ordem no `__init__` é sempre a mesma e é deliberada:

```python
self.ponte = PonteX(estado, parent=self)      # parentada: quem a mantém viva
self.rootContext().setContextProperty("ponte", self.ponte)   # ANTES do setSource
self.engine().addImportPath(str(DIRETORIO_QML))              # para o qmldir/Tema
self.setClearColor(QColor("#0d0d0d"))         # senão vaza branco nas bordas
self.setResizeMode(QQuickWidget.SizeRootObjectToView)
self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "XTab.qml")))
self._exigir_carregamento()                   # QQuickWidget NÃO levanta sozinho
```

Inverter `setContextProperty` e `setSource` não dá erro visível: o QML avalia as ligações
ao carregar, e uma `ponte` ausente naquele instante vira erro em **cada** binding — a aba
aparece, vazia, e o log enche.

`SobreTabQml` é a exceção do conjunto: construtor sem `estado`, sem contrato e sem fallback
de Widgets, porque é a única aba de que se pode abrir mão (D-51).

## Armadilhas de PySide6 e QML

Estas são as que um modelo de linguagem erra por hábito, com o que acontece de fato aqui.

**1. Sintaxe de PyQt vazando no PySide.** Aqui é PySide6, sempre. `Signal`/`Slot`/`Property`
de `PySide6.QtCore` — nunca `pyqtSignal`, `pyqtSlot`, `pyqtProperty`, nunca
`from PyQt5/PyQt6 import`. `QVariant`, `sip` e `.exec_()` são PyQt-ismos; este código usa
`app.exec()`.

**2. `@Property` sem `notify=`.** Compila, roda e a tela **congela naquele valor** sem um
único aviso. É a falha mais cara aqui, porque a arquitetura inteira depende de ligação viva:
`checked: ponte.modo === "teste"` só funciona porque `modo` declara `notify=mudou`. Toda
`@Property` das quatro pontes tem `notify`. Se você adicionar uma sem, o bug aparece como
"o botão não atualiza" e ninguém vai olhar para a propriedade.

**3. Objeto coletado pelo GC.** O `setContextProperty` **não** toma posse do objeto. Um
`self.rootContext().setContextProperty("ponte", PonteGeral(estado))` sem guardar a
referência dá tela em branco e erro de propriedade nula no QML, de forma intermitente. Por
isso aqui a ponte é sempre **atributo** (`self.ponte`) **e** parentada (`parent=self`).
Mesma coisa para diálogos, `QThread` e timers criados dentro de método.

**4. O lado espelhado: objeto C++ já destruído.** Se a ponte sobreviver ao widget e
continuar inscrita no `EstadoApp`, cada mudança de estado estoura
`RuntimeError: Internal C++ object already deleted` — e o `EstadoApp` engole a exceção por
desenho, então isso não aparece como falha, aparece como traceback no log a cada clique.
É para isso que existe `ponte.desligar()`, chamado no `destroyed` **e** no caminho de erro
antes do `raise`. Toda ponte nova precisa dos dois.

**5. Lista mutada sem avisar.** Não existe `QAbstractListModel` neste projeto. As listas vão
como `@Property(list, notify=...)` devolvendo **lista nova** de dicts, e o QML faz
`Repeater { model: ponte.saude }`. A armadilha aqui não é `beginInsertRows` — é `.append()`
na lista interna sem emitir o sinal, que não redesenha nada. Ou, pior, devolver
`self._saude` em vez de uma cópia: o QML passa a segurar a mesma lista e a troca deixa de
ser detectável. Sempre reconstrua e sempre emita.
Se algum dia uma lista aqui ficar grande o bastante para justificar `QAbstractListModel`,
aí valem as regras dele: `beginInsertRows`/`endInsertRows` em volta de toda inserção,
`beginResetModel`/`endResetModel` para troca em bloco, e `roleNames()` — mutar as linhas
por fora dá crash ou delegate fantasma, não exceção. Mas isso é decisão nova, não refactor
de rotina.

**6. Bloquear a thread de UI.** A engine é `GestureEngine(QThread)` e a conexão com o OBS é
`OBSConnectThread(QThread)`, criada por tentativa. Nada de `time.sleep`, requisição de rede
ou `cv2`/MediaPipe dentro de slot da UI. **A engine não toca em widget nem em ponte** — ela
só emite `Signal`, e a janela reage. O único `wait()` bloqueante autorizado está em
`ui/main_window.py:96`, ao destruir a janela, porque uma `QThread` viva na hora do fim
derruba o processo.

**7. Erro de QML não derruba o processo — nem sequer levanta.** `QQuickWidget` com `.qml`
ausente ou com erro de sintaxe registra o erro e fica **em branco**. Sem o
`_exigir_carregamento()` que checa `status() != QQuickWidget.Error` e faz `raise`, a falha
mais provável (os `.qml` fora do bundle) daria uma aba vazia em vez do fallback, e o
`try/except` de `setup_mixin` nunca dispararia. Se você criar uma aba QML, copie essa
checagem. E lembre: **o pytest não carrega QML nenhum** — teste verde não diz nada sobre a
interface.

**8. Enum com escopo.** Em PySide6 6.8 `QQuickWidget.Error` resolve na **classe**, mas
`widget.Error` na instância levanta `AttributeError`. Use a forma da classe, ou
`QQuickWidget.Status.Error`.

**9. `QtQuick.Controls` genérico.** O QML aqui importa **sempre**
`import QtQuick.Controls.Basic`, e `main.py:20` faz `QQuickStyle.setStyle("Basic")` antes do
`QApplication` e antes de qualquer coisa de QtQuick. "Basic" é o único estilo que deixa
sobrescrever `background` e `contentItem`; nos estilos nativos o Qt ignora a customização e
volta o problema do QSS, que é pedaço do controle vindo da plataforma (D-49). Import sem o
`.Basic` reintroduz isso em silêncio.

## Antes de responder — fluxo obrigatório

Nesta ordem. Se pulou um passo, diga que pulou.

1. **`git status` e `git log --oneline -5`.** O checkout já esteve 4 meses atrás do remoto.
2. **Leia `.planning/DECISIONS.md`** antes de chamar qualquer coisa de bug ou inconsistência.
   O arquivo é append-only e a maior parte das estranhezas está explicada lá com um `D-xx`.
3. **Rode os testes** se tocou em `core/`, `engine/`, `actions/`, `integrations/` ou nos
   aliases:

   ```powershell
   .venv\Scripts\python.exe -m pytest tests/ -q
   ```

4. **Rode o smoke headless de QML** se tocou em qualquer `.qml`, em `ui/qml/*.py` ou em
   `ui/tabs/*_qml.py`. Nenhum teste do pytest carrega QML; sem isto, um erro de sintaxe no
   `.qml` passa direto.

   PowerShell:

   ```powershell
   $env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python.exe -c "import sys; from PySide6.QtQuickControls2 import QQuickStyle; QQuickStyle.setStyle('Basic'); from PySide6.QtWidgets import QApplication; from PySide6.QtQuickWidgets import QQuickWidget; app=QApplication(sys.argv); from core.estado_app import EstadoApp; from ui.main_window import MainWindow; e=EstadoApp({}, [n for n,_ in MainWindow.ALL_GESTURES]); from ui.tabs.geral_tab_qml import GeralTabQml; from ui.tabs.gestos_tab_qml import GestosTabQml; from ui.tabs.obs_tab_qml import ObsTabQml; from ui.tabs.sobre_tab_qml import SobreTabQml; abas=[GeralTabQml(e), GestosTabQml(e), ObsTabQml(e), SobreTabQml()]; [print(type(w).__name__, 'ok') if w.status()!=QQuickWidget.Error else sys.exit(str([x.toString() for x in w.errors()])) for w in abas]; print('SMOKE OK')"
   ```

   bash / Git Bash:

   ```bash
   QT_QPA_PLATFORM=offscreen ./.venv/Scripts/python.exe -c "import sys; from PySide6.QtQuickControls2 import QQuickStyle; QQuickStyle.setStyle('Basic'); from PySide6.QtWidgets import QApplication; from PySide6.QtQuickWidgets import QQuickWidget; app=QApplication(sys.argv); from core.estado_app import EstadoApp; from ui.main_window import MainWindow; e=EstadoApp({}, [n for n,_ in MainWindow.ALL_GESTURES]); from ui.tabs.geral_tab_qml import GeralTabQml; from ui.tabs.gestos_tab_qml import GestosTabQml; from ui.tabs.obs_tab_qml import ObsTabQml; from ui.tabs.sobre_tab_qml import SobreTabQml; abas=[GeralTabQml(e), GestosTabQml(e), ObsTabQml(e), SobreTabQml()]; [print(type(w).__name__, 'ok') if w.status()!=QQuickWidget.Error else sys.exit(str([x.toString() for x in w.errors()])) for w in abas]; print('SMOKE OK')"
   ```

   Saída esperada: as quatro abas com `ok` e `SMOKE OK` no fim. Rode **da raiz do repo** —
   o `sys.path` depende do diretório atual. `EstadoApp({}, ...)` usa config vazia de
   propósito, para não depender do `config.json` da máquina. `SobreTabQml()` não recebe
   `estado`, ao contrário das outras três.

5. **`QT_QPA_PLATFORM=offscreen` é o único jeito de exercitar Qt sem janela.** Vale para
   qualquer verificação de UI que você inventar, não só para o smoke acima.
6. **O que não dá para verificar, diga que não verificou.** Câmera, VCam, OBS e Linux não
   são exercitáveis aqui.

## Convenções do código

- **Domínio em português, estrutura em inglês.** Classes e módulos em inglês
  (`GestureEngine`, `HandTracker`); métodos e variáveis de domínio em português
  (`processar`, `detectar`, `ler_frame`, `trocar_cena`). Comentários em português.
  Mantenha o padrão — não "traduza" código existente.
- **No QML e nas pontes, o português vai até o nome do componente e da propriedade.**
  Componentes: `BotaoAcao`, `Deslizante`, `PainelRolavel`, `CapturaDeAtalho`. Propriedades
  e slots expostos: camelCase português — `maxMaos`, `ajudaDoModo`, `corDaLatencia`,
  `escolherResolucao`. Sinais de intenção no particípio: `modoPedido`, `resolucaoPedida`,
  `maosPedidas`.
- Logging via `util.logger.get_logger(__name__)`. Nada de `print`.
- A engine roda numa `QThread` e conversa com a UI só por `Signal`. Não toque em widget
  de dentro da engine.
- Docstring de módulo explica **por que**, não o que, e cita o `D-xx` quando existe. É o
  padrão de todo arquivo novo aqui. Comentário que só reescreve a linha abaixo não entra.

## Regras rígidas

Derivadas do que este código já faz. Quebrar qualquer uma é sair do padrão, não "outro
estilo válido".

1. **Toda `@Property` exposta ao QML é somente leitura e declara `notify=`.** Nenhuma das
   quatro pontes tem setter de propriedade. Ver `ui/qml/ponte.py`.
2. **Tela → estado passa por `@Slot` que emite sinal de intenção, nunca por propriedade
   gravável.** O motivo está no cabeçalho de `ui/qml/ponte.py`: alguns cliques têm
   consequência além de guardar um valor (trocar o número de mãos pede confirmação e
   reinicia a captura, D-06), e quem decide isso é o Python, não a view.
3. **Um `mudou = Signal()` grosso por ponte, mais os finos que já existem.** Não crie um
   sinal por propriedade. A escolha está comentada em `ui/qml/ponte.py:45` — "a aba é
   pequena e redesenhar tudo é barato".
4. **A ponte é atributo, é parentada, e tem `desligar()`.** `PonteX(estado, parent=self)`,
   `self.destroyed.connect(lambda *_: self.ponte.desligar())`, e `desligar()` também antes
   de qualquer `raise` no `__init__`.
5. **Getter de lista devolve lista/dicts novos, e quem altera emite o sinal.**
   `return list(self._cameras)`, nunca `return self._cameras`.
6. **Aba QML nova checa `status()` e levanta.** Copie `_exigir_carregamento()`. Sem isso o
   fallback do `setup_mixin` não existe na prática.
7. **Nada fora de `plataforma/` importa API de sistema.** Um `import winsound` no topo de um
   módulo da cadeia normal derruba o app antes de a janela abrir. `tests/test_plataforma.py`
   vigia isso (D-42).
8. **`core/estado_app.py` não importa Qt.** É o que o torna testável sem abrir janela e o
   que permitiu a migração para QML sair barata (D-47). Não "melhore" transformando em
   `QObject`.
9. **Os mixins da janela falam com a aba pelo contrato, nunca com o widget.** Nada de
   `self.geral_tab.algum_botao.setEnabled(...)`. Se falta um verbo, adicione ao contrato em
   `ui/tabs/geral_contrato.py` **e** às duas implementações.
10. **Degradar é permitido; degradar em silêncio, não.** Toda queda para o modo antigo entra
    em `_QUEDAS` e chega ao usuário — empacotado não há console, e o log sozinho não avisa
    ninguém. Mesma regra do D-29 e do D-39.
11. **`except Exception as exc` sempre com `logger.error`/`logger.exception` e uma saída
    definida.** Exceção tipada (`FalhaAoSalvar`) quando o chamador precisa decidir; frase
    acionável para o usuário quando ele precisa agir (`_classificar_erro` em
    `integrations/obs_connect_thread.py`). `except: pass` não existe aqui.
12. **Escrita de config é atômica** — temporário no mesmo diretório e `os.replace` (D-22).
    Não substitua por `open(..., "w")` direto.
13. **`version.py` é bumpado à mão**, junto com a seção do `CHANGELOG.md` e a tag
    `v<versão>`. Os três precisam concordar. Não derive versão do git (D-51).

## Testes

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

251 testes, ~4 s, sem webcam e sem OBS. Rode antes de commitar qualquer mudança em
`core/`, `engine/` ou nos aliases.

- `tests/` — testes automatizados (pytest). `tests/maos_sinteticas.py` monta os 21
  landmarks a partir de uma descrição legível, sem precisar de câmera.
- `teste/` — scripts **manuais** antigos, que exigem webcam e OBS ligados. Não são
  coletados pelo pytest. Não confunda os dois.
- Não há `pytest-qt` nem fixture de `QApplication`. Quem precisa de Qt define
  `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` **no topo do módulo**, antes de
  importar PySide6 — é o que `tests/test_hotkeys.py:13` faz.
- **Cobertura de QML: quase zero.** `tests/test_shell_novo.py` cobre a fronteira
  Python↔QML da casca nova (preview, chips, adaptadores), mas nenhum teste carrega um
  `.qml`. É por isso que o smoke headless é passo obrigatório, e não sugestão.
- **"Carrega" não é "funciona".** O smoke prova que a árvore monta; ele não exercita
  nada que só acontece com dado passando. Foi assim que o preview quebrou a cada quadro
  com o smoke verde. Ver PITFALLS QML-02.

Deps de desenvolvimento em `requirements-dev.txt`, separadas das de runtime.

Ao mexer no detector, prefira **adicionar um caso** em `tests/maos_sinteticas.py` a
testar na mão. E confira que o teste novo falha se você reverter a mudança — teste que
passa nos dois estados não está testando nada.

## Ambiente

- **Python 3.10.11.** É o que o `requirements.txt` declara e contra o que tudo está pinado.
- `mediapipe==0.10.14` é pin rígido — não atualize sem uma decisão nova (D-04).
- **Validado só no Windows.** Existe implementação Linux (`plataforma/_linux.py`, D-46),
  mas ela nunca rodou em Linux de verdade — os testes cobrem a montagem do comando, não o
  efeito. Não afirme que o Linux funciona; diga que está escrito e não verificado.
- Nada de API de sistema fora de `plataforma/` (D-42). Um `import winsound` no topo de um
  módulo da cadeia normal derruba o app antes de a janela abrir. `tests/test_plataforma.py`
  vigia isso.
- `config.json` **não é versionado**. O app o regenera completo no primeiro boot.

## Invariantes

Marcados como `FIXA` em `DECISIONS.md`. Quebrar qualquer um destes é regressão conhecida:

- Inversão de handedness acontece **só** dentro de `HandTracker.processar()` (D-01)
- `model_complexity=0` no MediaPipe Hands (D-04)
- `OBSController.connect()` faz handshake com `get_version()` antes de marcar conectado (D-12)

## Como responder

- **Direto, sem preâmbulo.** Nada de "Ótima pergunta", "Vou analisar o projeto", "Claro!".
  Comece pela resposta.
- **Diga o que você verificou e como.** "Rodei os 240 testes, passam" e "li
  `ui/qml/ponte.py`" são afirmações diferentes de "deve funcionar". Nomeie o comando ou o
  arquivo. Se não rodou, diga que não rodou.
- **Separe verificado de deduzido.** Câmera, VCam, OBS e Linux não são exercitáveis nesta
  máquina — sobre eles, diga que a mudança está escrita e não verificada.
- **Antes de chamar algo de bug, procure o `D-xx`.** Se `DECISIONS.md` explica, cite a
  decisão em vez de propor "consertar".
- Citação de código como `arquivo.py:linha`.
- Sem resumo do que você acabou de fazer quando o diff já mostra. Sem lista de próximos
  passos que ninguém pediu.

## Ao fechar uma sessão

- Atualize `.planning/STATE.md`: mova o item entregue para a tabela com o **SHA do commit**,
  e tire-o do "Próximo".
- Registrou uma escolha que um leitor futuro acharia arbitrária? Vai para `DECISIONS.md`
  como entrada nova. O arquivo é append-only.
- Plano detalhado de fase vive em `.planning/active/` e é **apagado** quando a fase fecha —
  o commit é o registro. Decisão e pitfall são permanentes.
