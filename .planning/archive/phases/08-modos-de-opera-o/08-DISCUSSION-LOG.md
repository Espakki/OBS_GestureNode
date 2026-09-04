# Phase 8: Modos de Operação - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 8-Modos de Operação
**Areas discussed:** Padrão de fábrica, Escopo do modo Teste, User story do modo Manual, Layout e labels dos 3 modos

---

## Padrão de fábrica

**Conflito identificado:** REQUIREMENTS.md MODE-04 dizia "Teste" como padrão. Todo capturado + STATE.md Key Decision diziam "Automático".

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| Automático | config.json default = 'automatico'. Engine tolera OBS ausente sem crash (Phase 3). Zero configuração extra. | ✓ |
| Teste | config.json default = 'teste'. Sempre seguro na primeira execução. Requer troca manual para usar em live. | |

**Escolha:** Automático como padrão de fábrica.
**Notas:** SC5 do roadmap ("primeira execução em Teste") substituída. MODE-04 do REQUIREMENTS.md sobreposto. Decisão motivada pelo objetivo de zero fricção: "abre, configura gestos, aperta iniciar".

---

## Escopo do modo Teste

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| Bloquear tudo + mensagem clara | Sem OBS, sem hotkeys, sem áudio. Status bar exibe "Modo Teste — ações desativadas". | ✓ |
| Bloquear só OBS | Hotkeys e áudio continuam. Comportamento atual da v1.1. | |

**Escolha:** Bloquear tudo + mensagem clara no status bar.
**Notas:** Usuário quis a opção 1 com feedback visual passivo (não modal). Mudança comportamental em relação à v1.1 onde hotkeys ainda disparavam em modo teste.

---

## User story do modo Manual

**Pergunta 1 — para qual público:**

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| Power user com problema de VCam | Manual = Automático sem VCam auto-start. Para conflito de driver ou VCam incompatível. | ✓ |
| Cenário de teste antes de ir ao vivo | Modo intermediário entre Teste e Automático. | |
| Ambos os cenários | UI descreve comportamento, não o porquê. | |

**Pergunta 2 — OBS conecta automaticamente ou só ao clicar:**

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| Só ao clicar | Usuário controla quando conectar. | |
| Auto-conecta ao iniciar (sem VCam) | Manual = Automático sem VCam. | ✓ |

**Escolha:** Manual auto-conecta WebSocket (igual ao Automático) + sem VCam.
**Notas:** Usuário confirmou: "se conecta com o websocket? se sim, se conecta automático, sem o VCam pois daria conflito". Matriz final: Teste=nada, Manual=WebSocket+hotkeys sem VCam, Automático=tudo.

---

## Layout e labels dos 3 modos

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| 3 botões toggle em linha | Expande padrão atual. 3 QPushButton checkable lado a lado. | ✓ |
| 3 radio buttons verticais | Coluna com espaço para descrição por modo. Muda o padrão visual. | |
| Você decide | Deixar para o implementador. | |

**Labels:**

| Opção | Descrição | Selecionada |
|-------|-----------|-------------|
| Teste / Manual / Automático | Labels diretos com tooltip explicando. | ✓ |
| Treino / Controlado / Ao Vivo | Nomes orientados ao contexto do streamer. | |
| Você decide | Qualquer um serve. | |

**Escolha:** 3 botões toggle em linha com labels "Teste / Manual / Automático".

---

## Claude's Discretion

- Texto do `mode_help_label` (abaixo dos botões) — implementador escolhe a descrição orientada ao streamer para cada modo.
- Posicionamento exato da mensagem "Modo Teste — ações desativadas" dentro do status bar existente.
- Lógica de migração silenciosa de `"test"` → `"teste"` e `"obs"` → `"automatico"` no carregamento do config.

---

## Deferred Ideas

- Configurações de câmera → painel "Avançadas" oculto — Phase 14
- OBS Virtual Cam sub-modos (auto/manual) dentro de Configurações Avançadas — Phase 13
- Suprimir preview ao minimizar janela (modo OBS ativo) — Phase 15
- Detecção de 2 mãos e gestos combinados — Phase 9
