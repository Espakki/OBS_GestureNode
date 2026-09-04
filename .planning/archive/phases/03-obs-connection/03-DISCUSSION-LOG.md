# Phase 3: OBS Connection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-24
**Phase:** 3-OBS Connection
**Areas discussed:** Arquitetura do thread OBS, Localização do status OBS, Escopo das mensagens de erro, TODO de lag em resoluções altas

---

## Arquitetura do thread OBS

### Q1: Arquitetura do thread

| Option | Description | Selected |
|--------|-------------|----------|
| OBSConnectThread reutilizável | Classe QThread dedicada com signals, compartilhada pelo botão e pela engine | ✓ |
| Dois fixes independentes | Corrigir botão e engine separadamente, com lógica duplicada | |
| Você decide | Claude escolhe | |

**User's choice:** OBSConnectThread reutilizável
**Notes:** Nenhuma nota adicional.

### Q2: Ciclo de vida do thread

| Option | Description | Selected |
|--------|-------------|----------|
| Criado por tentativa, destruído ao completar | Instância nova a cada tentativa | ✓ |
| Thread persistente com fila de comandos | Thread vivo durante toda a sessão, aceita comandos | |

**User's choice:** Criado por tentativa, destruído ao completar

### Q3: UX durante tentativa

| Option | Description | Selected |
|--------|-------------|----------|
| Botão desabilitado + texto 'Conectando...' | test_obs_button.setEnabled(False) + label | ✓ |
| Botão desabilitado + spinner animado | QMovie/CSS — requer asset externo, escopo Phase 6 | |

**User's choice:** Botão desabilitado + texto 'Conectando...'

---

## Localização do status OBS

### Q1: Onde fica o indicador persistente

| Option | Description | Selected |
|--------|-------------|----------|
| Status bar no rodapé (abaixo das abas) | QLabel ao lado do "Status: Rodando" existente | ✓ |
| Health panel no GeralTab (health_obs) | Só visível na aba Geral | |
| Widget fixo acima das abas | Mais proeminente, requer reestruturação do MainWindow | |

**User's choice:** Status bar no rodapé

### Q2: Manter OBSTab label?

| Option | Description | Selected |
|--------|-------------|----------|
| Manter os dois | Rodapé compacto + OBSTab com mensagem detalhada | ✓ |
| Só o rodapé | Remove obs_status_label da OBSTab | |

**User's choice:** Manter os dois

---

## Escopo das mensagens de erro

### Q1: Quantos tipos cobrir

| Option | Description | Selected |
|--------|-------------|----------|
| 4 tipos | ConnectionRefused, Auth, Timeout, Host inválido | ✓ |
| 2 tipos (só os dos success criteria) | Conexão recusada + senha, resto genérico | |

**User's choice:** 4 tipos

### Q2: Onde exibir erro quando usuário está em outra aba

| Option | Description | Selected |
|--------|-------------|----------|
| Só no rodapé (resumida), OBSTab para detalhes | Fluxo natural já leva à aba OBS | ✓ |
| QMessageBox (pop-up) | Modal garante visibilidade imediata | |

**User's choice:** Só no rodapé (resumida), detalhes na OBSTab

---

## TODO de lag em resoluções altas

| Option | Description | Selected |
|--------|-------------|----------|
| Manter como TODO independente | Escopo de engine, não OBS; investigar na Phase 4+ | ✓ |
| Dobrar na Phase 3 como investigação | Aumenta escopo da fase | |

**User's choice:** Manter como TODO independente

---

## Claude's Discretion

- Classificação de exceções do obsws-python: isinstance() checks; fallback para string matching se a lib não expor tipos específicos
- Posicionamento do QLabel no rodapé: ao lado direito do status_label existente
- Localização do arquivo OBSConnectThread: integrations/obs_controller.py ou novo integrations/obs_connect_thread.py

## Deferred Ideas

- Reconexão automática ao OBS em mid-session — v2 requirement explícito; arquitetura de OBSConnectThread deve permitir extensão futura
- Spinner animado durante conexão — escopo de Phase 6 (UI Visual Redesign)
