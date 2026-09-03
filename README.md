# OBS GestureNode

Controle o OBS Studio com gestos de mão pela webcam. Detecta gestos via MediaPipe e dispara
ações configuráveis: troca de cena no OBS, atalho de teclado global ou som.

Interface PySide6 com tema escuro, preview ao vivo com esqueleto da mão, onboarding no
primeiro uso e configuração por gesto (tempo de espera, cooldown e ação).

## Requisitos

- **Windows** — o disparo de atalhos usa `SendInput` (`user32.dll`), sons usam `winsound` e
  a enumeração de câmeras usa `pygrabber` (DirectShow)
- **Python 3.10.11** — versão contra a qual as dependências estão pinadas
- OBS Studio com o **WebSocket server** habilitado (Ferramentas → Configurações do WebSocket),
  necessário nos modos `manual` e `automatico`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Rodando

```bash
python main.py
```

Na primeira execução o app cria um `config.json` completo com os padrões e abre o
onboarding. Não é preciso copiar nada.

## Modos de operação

Definidos em `config.json` na chave `modo`, trocáveis pela aba Geral:

| Modo | O que faz |
|---|---|
| `teste` | Só reconhecimento de gestos, sem tocar no OBS. Bom pra calibrar. |
| `manual` | Conecta no OBS e dispara as ações. Câmera virtual desligada. |
| `automatico` | Padrão. Igual ao manual, mas também liga a câmera virtual. |

Valores antigos são migrados automaticamente no boot: `test` → `teste`, `obs` → `automatico`
(veja `ui/mixins/config_mixin.py`). Qualquer valor desconhecido vira `automatico`.

## Configuração

O `config.json` é **estado local do usuário** e não é versionado — contém a senha do
WebSocket do OBS e paths da sua máquina. O app o reescreve a cada mudança na interface,
então ajuste tudo pela UI, não na mão.

### Anti-disparo acidental

Além do `hold_time` por gesto, a engine tem um `GestureStabilityMonitor` que só libera a
ação quando a mão está de fato parada:

- **Motion check** — os landmarks precisam se mover menos que `motion_pixel_threshold`
  pixels por `stability_min_frames` frames consecutivos
- **Velocity check** (`check_velocity_trend`) — o movimento precisa estar *diminuindo*,
  sinalizando intenção de parar em vez de um gesto de passagem

Isso evita que gesticular durante uma conversa troque sua cena no meio da live.

## Build

```bash
pyinstaller main.spec
```

Gera `dist/main/`. O spec empacota a pasta `assets/` e faz `collect_all('mediapipe')`, que é
necessário porque o MediaPipe carrega os modelos `.tflite` como data files.

## Estrutura

```
main.py                    entrypoint: carrega config, aplica tema e abre a janela
core/
  camera.py                captura da webcam, backend DirectShow e câmera virtual
  hand_tracker.py          wrapper do MediaPipe Hands, resolução de processamento fixa
  gesture_detector.py      classifica os gestos por geometria dos landmarks
  gesture_aliases.py       fonte única de verdade: código interno -> nome de exibição
engine/
  gesture_engine.py        QThread com o loop principal, estabilidade e cooldown
actions/
  action_manager.py        executa cena / som / atalho (SendInput + fallback keyboard)
integrations/
  obs_controller.py        cliente obsws-python
  obs_connect_thread.py    conexão assíncrona, pra não travar a UI
ui/
  main_window.py           janela principal, composta pelos mixins
  mixins/                  responsabilidades por domínio: camera, config, engine,
                           gesture, health, obs, setup
  tabs/                    abas Geral, Gestos e OBS
  onboarding.py            assistente de primeiro uso
  presets.py               presets de configuração
  styles.py                stylesheet do tema escuro
util/
  hotkey_listener.py       captura de combinações de tecla na UI
  logger.py                logging centralizado
teste/                     scripts de teste manual (não são testes automatizados)
```
