---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-22
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Nenhum detectado — verificações manuais + smoke scripts Python |
| **Config file** | none — sem pytest.ini ou setup.cfg |
| **Quick run command** | `python -c "from core.gesture_aliases import GESTURE_ALIASES; print(GESTURE_ALIASES)"` |
| **Full suite command** | `python smoke_foundation.py` (criado na Wave 0 se desejado) |
| **Estimated runtime** | ~5 segundos (smoke manual) |

---

## Sampling Rate

- **After every task commit:** Verificar manualmente o comportamento descrito no critério da tarefa
- **After every plan wave:** Executar smoke script de importação + validar config.json + `pip check`
- **Before `/gsd-verify-work`:** Todos os Success Criteria do Roadmap devem ser TRUE
- **Max feedback latency:** ~30 seconds (verificações manuais rápidas)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|--------|
| 1-01-01 | 01 | 1 | DEP-02 | — | N/A | inspeção | `cat requirements.txt` (todas as linhas com `==`) | ⬜ pending |
| 1-01-02 | 01 | 1 | DEP-01 | — | N/A | comando | `pip install -r requirements.txt` em venv limpo | ⬜ pending |
| 1-02-01 | 02 | 1 | ENG-03 | — | N/A | smoke script | `python -c "from core.gesture_aliases import GESTURE_ALIASES; print(len(GESTURE_ALIASES))"` | ⬜ pending |
| 1-03-01 | 03 | 2 | ENG-04 | — | N/A | smoke manual | Editar gestos tab e geral tab alternadamente com engine rodando — sem KeyError | ⬜ pending |
| 1-04-01 | 04 | 2 | ENG-05 | — | N/A | smoke manual | Iniciar app de `C:\Windows\system32` — config.json NÃO criado lá | ⬜ pending |
| 1-05-01 | 05 | 2 | ENG-06 | — | N/A | smoke manual | Mover sliders 10s — config.json válido no path correto, sem arquivos temp | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Nenhum arquivo de test precisa ser criado para Phase 1 — todos os critérios são verificáveis manualmente ou por smoke scripts inline.
- Opcional: `smoke_foundation.py` na raiz do projeto para verificar import de `core.gesture_aliases`, validade do config.json e sintaxe do requirements.txt.

*Existing infrastructure: nenhuma. Wave 0 apenas confirma imports funcionam após edições.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App iniciado de C:\Windows\system32 carrega config do path correto | ENG-05 | Requer abrir processo em CWD diferente | Abrir terminal como Admin em C:\Windows\system32, rodar `python D:\...\main.py`, verificar que config.json não é criado em system32 |
| Mover sliders 10s não corrompe config.json | ENG-06 | Requer interação real com UI | Abrir app, mover qualquer slider rapidamente por 10s, abrir config.json e verificar que é JSON válido |
| Editar duas abas simultaneamente não produz KeyError | ENG-04 | Requer concorrência real UI+Engine | Iniciar câmera, alternar entre aba Geral e aba Gestos editando campos, verificar sem crash nos logs |
| pip install em venv limpo sem erros | DEP-01, DEP-02 | Requer ambiente novo | `python -m venv test_env && test_env\Scripts\activate && pip install -r requirements.txt` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
