# OBS GestureNode

Controle o OBS Studio com gestos de mão pela webcam — sem tirar as mãos do controle, do
teclado ou do mouse.

Você configura qual gesto dispara qual ação, e o app faz o resto: reconhece o gesto pela
câmera e troca a cena no OBS, dispara um atalho de teclado ou toca um som.

> **Estado:** funcional e em uso. Windows por enquanto; o suporte a Linux está mapeado mas
> ainda não implementado.

---

## O que ele faz

- **14 gestos** reconhecidos pela webcam: joinha, deslike, V, punho, mão aberta, OK,
  arminha, escoteiro, rock, três, quatro, apontando, me liga e dedo do meio
- **Três ações por gesto**, combináveis: trocar cena no OBS, disparar atalho de teclado,
  tocar um `.wav`
- **Duas mãos ao mesmo tempo** — você não precisa se preocupar com qual é a "mão certa";
  vale a primeira que fizer o gesto
- **Proteção contra disparo acidental**: o gesto só conta depois de ficar parado por um
  tempo que você define
- **Câmera virtual** para o OBS, em resolução nativa

## Requisitos

- **Windows** — a injeção de atalhos e a captura usam APIs do sistema
- **OBS Studio** com o WebSocket server ligado (Ferramentas → Configurações do WebSocket),
  se for usar troca de cena
- Uma **webcam**

## Como usar

Baixe o executável, abra e siga o onboarding. Na primeira execução o app cria a
configuração sozinho — não é preciso mexer em arquivo nenhum.

### Os três modos

| Modo | O que faz | Quando usar |
|---|---|---|
| **Teste** | Reconhece gestos mas não executa nada | Calibrar seus gestos sem risco |
| **Manual** | Conecta ao OBS e executa as ações | Se a câmera virtual der conflito |
| **Automático** | Igual ao manual, mais a câmera virtual | O padrão, e o que a maioria quer |

### Configurando um gesto

Na aba **Gestos**, escolha o gesto, marque a ação (cena, atalho ou som) e preencha. Dois
ajustes importam:

- **Tempo de resposta** — quanto você precisa segurar o gesto. Mais alto = menos disparo
  acidental durante uma conversa.
- **Cooldown** — quanto tempo até o mesmo gesto poder disparar de novo.

### Se algo não funcionar

O app avisa na tela, não só no log:

- **Botão de FPS ou resolução cinza** — sua câmera não oferece aquele modo. A faixa amarela
  na aba Geral diz qual é o limite dela, e o botão *Usar configuração recomendada* escolhe
  o melhor modo para o seu caso.
- **"OBS não tem a cena X"** — o nome da cena no gesto não existe no OBS. Corrija e tente
  de novo; não precisa reiniciar.
- **Câmera não abre** — feche outros programas que possam estar usando a webcam. Se estiver
  no modo automático, feche o OBS antes de iniciar o app e abra depois.

---

## Desenvolvimento

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python main.py
```

**Python 3.10.11** — é contra ela que as dependências estão pinadas.

### Testes

```bash
.venv\Scripts\python.exe -m pytest tests/ -q
```

184 testes, ~2s, **sem precisar de webcam nem OBS**. `tests/maos_sinteticas.py` monta os 21
landmarks de uma mão a partir de uma descrição legível, então o detector é testável sem
câmera.

Atenção: `tests/` são os testes automatizados; `teste/` (singular) são scripts manuais
antigos, que exigem hardware ligado e não são coletados pelo pytest.

### Build

```bash
pyinstaller main.spec
```

Gera `dist/main/`. O PyInstaller **não faz cross-compile**: o build do Windows sai numa
máquina Windows, e o do Linux numa Linux.

### Estrutura

```
main.py                    entrypoint: carrega config, aplica tema, abre a janela
plataforma/                tudo que depende do sistema operacional
  _windows.py              winsound + SendInput (só importado no Windows)
  _generico.py             fallback de teclado; base da futura implementação Linux
core/
  camera.py                captura via PyAV, câmera virtual, retry e fallback de FPS
  capacidades_camera.py    o que a câmera aceita de verdade, perguntado ao sistema
  hand_tracker.py          wrapper do MediaPipe Hands
  gesture_detector.py      classifica os gestos por geometria dos landmarks
  gesture_aliases.py       fonte única: código interno -> nome de exibição
  modos.py                 fonte única do modo de operação
engine/
  gesture_engine.py        QThread com o loop principal, estabilidade e despacho
actions/
  action_manager.py        executa cena / som / atalho — sem saber o sistema
integrations/
  obs_controller.py        cliente obsws-python
  obs_connect_thread.py    conexão assíncrona, para não travar a UI
ui/
  main_window.py           janela principal, composta por mixins
  mixins/                  camera, config, engine, gesture, health, obs, setup
  tabs/                    abas Geral, Gestos e OBS
  onboarding.py            assistente de primeiro uso
  styles.py                stylesheet do tema escuro
util/
  caminhos.py              onde o config mora em cada sistema
  logger.py                logging centralizado
tests/                     testes automatizados (pytest)
teste/                     scripts manuais antigos — exigem webcam e OBS
.planning/                 estado do projeto, decisões e armadilhas
```

### Antes de mexer

Leia [`.planning/DECISIONS.md`](.planning/DECISIONS.md). Várias escolhas parecem
inconsistência até você ver o motivo registrado — e mais de uma já foi "corrigida" por
engano por falta dessa leitura. [`.planning/STATE.md`](.planning/STATE.md) diz onde o
projeto está, e [`CLAUDE.md`](CLAUDE.md) resume as convenções e os invariantes.

---

## Licença

[MIT](LICENSE) — use, modifique e distribua à vontade, inclusive comercialmente, mantendo
o aviso de copyright.
