# CLAUDE.md

App desktop Windows (PySide6) que controla o OBS Studio por gestos de mão via webcam.
MediaPipe para detecção, PyAV para captura, `obsws-python` para o OBS.

## Comece por aqui

1. **`.planning/STATE.md`** — onde o projeto está. É o único arquivo que diz status.
2. **`.planning/DECISIONS.md`** — leia antes de chamar qualquer coisa de bug. Várias
   escolhas parecem inconsistência até você ver o motivo registrado.
3. **`.planning/PITFALLS.md`** — antes de encostar em câmera, MediaPipe ou VCam.
4. **`.planning/BACKLOG.md`** — o que está aberto e por quê.

Se o repo esteve parado, **rode `git pull` antes de analisar qualquer coisa.** Já houve um
caso do checkout local estar 4 meses atrás do remoto, e toda a análise saiu errada.

## Ambiente

- **Python 3.10.11.** É o que o `requirements.txt` declara e contra o que tudo está pinado.
- `mediapipe==0.10.14` é pin rígido — não atualize sem uma decisão nova (D-04).
- Windows-only por design: `SendInput`/`ctypes` para hotkeys, `winsound` para áudio,
  DirectShow para câmera.
- `config.json` **não é versionado**. O app o regenera completo no primeiro boot.

## Convenções do código

- **Domínio em português, estrutura em inglês.** Classes e módulos em inglês
  (`GestureEngine`, `HandTracker`); métodos e variáveis de domínio em português
  (`processar`, `detectar`, `ler_frame`, `trocar_cena`). Comentários em português.
  Mantenha o padrão — não "traduza" código existente.
- Logging via `util.logger.get_logger(__name__)`. Nada de `print`.
- A engine roda numa `QThread` e conversa com a UI só por `Signal`. Não toque em widget
  de dentro da engine.

## Invariantes

Marcados como `FIXA` em `DECISIONS.md`. Quebrar qualquer um destes é regressão conhecida:

- Inversão de handedness acontece **só** dentro de `HandTracker.processar()` (D-01)
- `model_complexity=0` no MediaPipe Hands (D-04)
- `OBSController.connect()` faz handshake com `get_version()` antes de marcar conectado (D-12)

## Ao fechar uma sessão

- Atualize `.planning/STATE.md`: mova o item entregue para a tabela com o **SHA do commit**,
  e tire-o do "Próximo".
- Registrou uma escolha que um leitor futuro acharia arbitrária? Vai para `DECISIONS.md`
  como entrada nova. O arquivo é append-only.
- Plano detalhado de fase vive em `.planning/active/` e é **apagado** quando a fase fecha —
  o commit é o registro. Decisão e pitfall são permanentes.
