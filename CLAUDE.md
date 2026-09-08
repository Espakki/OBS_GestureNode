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
- **Validado só no Windows.** Existe implementação Linux (`plataforma/_linux.py`, D-46),
  mas ela nunca rodou em Linux de verdade — os testes cobrem a montagem do comando, não o
  efeito. Não afirme que o Linux funciona; diga que está escrito e não verificado.
- Nada de API de sistema fora de `plataforma/` (D-42). Um `import winsound` no topo de um
  módulo da cadeia normal derruba o app antes de a janela abrir. `tests/test_plataforma.py`
  vigia isso.
- `config.json` **não é versionado**. O app o regenera completo no primeiro boot.

## Convenções do código

- **Domínio em português, estrutura em inglês.** Classes e módulos em inglês
  (`GestureEngine`, `HandTracker`); métodos e variáveis de domínio em português
  (`processar`, `detectar`, `ler_frame`, `trocar_cena`). Comentários em português.
  Mantenha o padrão — não "traduza" código existente.
- Logging via `util.logger.get_logger(__name__)`. Nada de `print`.
- A engine roda numa `QThread` e conversa com a UI só por `Signal`. Não toque em widget
  de dentro da engine.

## Testes

```bash
.venv\Scripts\python.exe -m pytest tests/ -q
```

229 testes, ~3s, sem webcam e sem OBS. Rode antes de commitar qualquer mudança em
`core/`, `engine/` ou nos aliases.

- `tests/` — testes automatizados (pytest). `tests/maos_sinteticas.py` monta os 21
  landmarks a partir de uma descrição legível, sem precisar de câmera.
- `teste/` — scripts **manuais** antigos, que exigem webcam e OBS ligados. Não são
  coletados pelo pytest. Não confunda os dois.

Deps de desenvolvimento em `requirements-dev.txt`, separadas das de runtime.

Ao mexer no detector, prefira **adicionar um caso** em `tests/maos_sinteticas.py` a
testar na mão. E confira que o teste novo falha se você reverter a mudança — teste que
passa nos dois estados não está testando nada.

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
