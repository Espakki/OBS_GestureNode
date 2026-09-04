---
status: diagnosed
phase: 03-obs-connection
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md
started: 2026-06-25T22:30:00-03:00
updated: 2026-06-25T22:45:00-03:00
---

## Current Test

[testing complete]

## Tests

### 1. OBSController.connect() elimina falso positivo (D1)
expected: OBSController.connect() chama get_version() antes de setar connected=True — falso positivo eliminado
result: pass
source: automated
coverage_id: D1

### 2. OBSConnectThread com signals corretos (D2)
expected: OBSConnectThread(QThread) existe com signals connected/failed/connecting e run() executando fora do main thread
result: pass
source: automated
coverage_id: D2

### 3. _classificar_erro() mapeia todos os tipos de erro (D3)
expected: _classificar_erro() classifica ConnectionRefusedError / TimeoutError / gaierror / OBSSDKError / fallback para mensagens acionáveis
result: pass
source: automated
coverage_id: D3

### 4. Footer OBS Status Visible
expected: Rodapé da MainWindow exibe label de status OBS (ex: "🔴 OBS: Desconectado") visível em todas as abas
result: pass

### 5. Botão "Testar conexão" não-bloqueante
expected: Com OBS offline, clicar "Testar conexão" não trava a janela — a UI permanece responsiva (é possível trocar de aba, mover a janela) enquanto a tentativa está em andamento
result: pass

### 6. Botão desabilitado durante tentativa
expected: Ao clicar "Testar conexão", o botão fica desabilitado imediatamente e só reabilita quando a tentativa conclui (sucesso ou falha)
result: issue
reported: "não sempre fica com a cor azul"
severity: major

### 7. Mensagem de erro acionável (OBS offline)
expected: Com OBS Studio fechado (ou host/porta errados), após clicar "Testar conexão" aparece mensagem específica (ex: "OBS inacessível — verifique se o OBS está aberto" ou "Conexão recusada") — não a mensagem genérica "Falha ao conectar OBS"
result: pass

### 8. Conexão bem-sucedida
expected: Com OBS Studio aberto e credenciais corretas (host/porta/senha), clicar "Testar conexão" → footer exibe "🟢 OBS: Conectado" e o log principal confirma a conexão
result: pass

### 9. Erro do startup da engine aparece no footer (03-03)
expected: Iniciar o modo "obs" da engine com OBS offline → footer exibe mensagem de erro acionável com prefixo "OBS:" (ex: "🔴 OBS: OBS inacessível") — não texto genérico
result: pass

## Summary

total: 9
passed: 8
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Ao clicar 'Testar conexão', o botão fica desabilitado imediatamente e só reabilita quando a tentativa conclui"
  status: failed
  reason: "User reported: não sempre fica com a cor azul"
  severity: major
  test: 6
  root_cause: "setEnabled(False) é chamado em main_window.py:991, mas ConnectionRefusedError é quase instantânea. O signal `failed` chega à fila do Qt antes do primeiro repaint do estado desabilitado — setEnabled(True) é chamado antes do Qt pintar o botão cinza, os dois repaints coalescem e o usuário nunca percebe a mudança visual."
  artifacts:
    - path: "ui/main_window.py"
      issue: "linha 991: setEnabled(False) precisa de QApplication.processEvents() após para forçar repaint antes de thread.start()"
  missing:
    - "Adicionar QApplication.processEvents() após self.test_obs_button.setEnabled(False) (linha 991) para garantir que o botão repinte o estado desabilitado antes da thread iniciar"
  debug_session: ""
