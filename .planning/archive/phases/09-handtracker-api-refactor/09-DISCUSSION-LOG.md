# Phase 9: HandTracker API Refactor - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 9-HandTracker API Refactor
**Areas discussed:** Escopo de ações no modo 2 mãos, Widget '1 mão / 2 mãos' na aba Geral, Comportamento ao trocar 1↔2 mãos com engine rodando

---

## Escopo de ações no modo 2 mãos

| Option | Description | Selected |
|--------|-------------|----------|
| Cada mão dispara independente | Thumbs_up em qualquer mão dispara a binding configurada. Simples, consistente com modo 1 mão. Phase 10 adiciona gestos COMBINADOS como camada nova. | ✓ |
| Só tracking — sem dispatch | Phase 9 só habilita rastreamento e exibe labels. Dispatch de 2 mãos inteiramente na Phase 10. | |

**User's choice:** Cada mão dispara independente

| Option | Description | Selected |
|--------|-------------|----------|
| Dispara duas vezes (uma por mão) | Cada mão tem seu próprio cooldown. | |
| Dispara uma vez (primeira mão vence) | Cooldown compartilhado — se já disparou para esse gesto (qualquer mão), o cooldown bloqueia a segunda. | ✓ |
| Cooldown compartilhado por gesto | Mesma semântica que a opção anterior — `ultimo_disparo_por_gesto` shared. | |

**User's choice:** Dispara uma vez (primeira mão vence) — cooldown compartilhado por gesto

| Option | Description | Selected |
|--------|-------------|----------|
| Qualquer mão (binding por gesto, não por mão) | Thumbs_up na esquerda OU direita dispara a mesma binding. Compatível com configs existentes — zero migração. | ✓ |
| Bindings separadas por mão | Esquerda + thumbs_up é diferente de Direita + thumbs_up. Requer nova estrutura de config — melhor deixar para Phase 10/11. | |

**User's choice:** Qualquer mão — binding por gesto, não por mão

---

## Widget '1 mão / 2 mãos' na aba Geral

| Option | Description | Selected |
|--------|-------------|----------|
| 2 QPushButtons checkáveis | Mesmo padrão visual dos botões Teste/Manual/Automático em geral_tab.py:42-56. Consistente, sem novo widget. | ✓ |
| QCheckBox simples | Caixa '☑ Detectar 2 mãos'. Mais leve visualmente, menos espaço. Novo padrão na tab. | |
| QComboBox dropdown | Dropdown 'Número de mãos: [1 ▾]'. Mais explícito, preparado para '3+'. | |

**User's choice:** 2 QPushButtons checkáveis

| Option | Description | Selected |
|--------|-------------|----------|
| Logo abaixo do row de modo | Agrupar controles de operação juntos: Modo + Mãos. Fluxo natural de configuração. | ✓ |
| Acima das configurações de câmera | Antes de índice/resolução. Separa configurações de detecção das de câmera. | |
| Dentro de um grupo 'Detecção' | Criar QGroupBox 'Detecção' com hold_time + mãos. Mais organizado mas mudança de layout maior. | |

**User's choice:** Logo abaixo do row de modo

---

## Comportamento ao trocar 1↔2 mãos com engine rodando

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-restart automático | Engine para e reinicia automaticamente ao trocar. Status exibe 'Reiniciando...' durante a transição. | ✓ |
| Banner passivo 'Reinicie para aplicar' | Troca é salva mas não aplicada. Label amarela aparece. Usuário controla quando reiniciar. | |
| Bloquear seletor enquanto engine ativa | Botões '1 Mão / 2 Mãos' ficam desabilitados enquanto engine está rodando. | |

**User's choice:** Auto-restart automático

| Option | Description | Selected |
|--------|-------------|----------|
| Persiste no config, aplica no próximo Start | Engine já parada: salva max_maos no config.json; aplica no próximo Start. Sem restart desnecessário. | ✓ |
| Mesmo comportamento (sempre restart) | Comportamento idêntico independente do estado da engine. Mais simples mas restart desnecessário. | |

**User's choice:** Persiste no config, aplica no próximo Start

---

## Claude's Discretion

- Handedness inversion: aplicar em `HandTracker.processar()` (fix na fonte) — decisão técnica não perguntada ao usuário; pitfall já documentado em SUMMARY.md/STATE.md
- Labels de handedness no preview: parte do skeleton existente ou texto no frame; não UI overlay (Phase 12 trata isso)
- Status emit em 2 mãos: formato "Gesto Left: X | Right: Y" — implementação a critério do planner

## Deferred Ideas

- Gestos COMBINADOS (par esquerda+direita como unidade) → Phase 10
- Bindings separadas por mão (left_thumbs_up ≠ right_thumbs_up) → Phase 10/11
- Config schema v2 completo com `combined_bindings` → Phase 10 (GES-06, GES-07)
- Preview overlay com 2 barras de hold time independentes → Phase 12
