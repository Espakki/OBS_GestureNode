# teste/ — scripts manuais

**Não confunda com `tests/`**, que são os testes automatizados rodados pelo pytest.

O que sobrou aqui exige **hardware ligado** — webcam, OBS, ou os dois — e por isso não dá
para automatizar. Nenhum destes é coletado pelo pytest.

| Script | O que faz | Precisa de |
|---|---|---|
| `teste_cam.py` | Abre a câmera e mostra frames | Webcam |
| `test_obs.py` | Conecta no OBS e lista as cenas | OBS com WebSocket ligado |
| `smoke_phase3.py` | Smoke da conexão OBS assíncrona | OBS |
| `teste_pyav_vs_opencv.py` | Benchmark que motivou a migração para PyAV | Webcam |

O benchmark fica por valor histórico: foi ele que mediu a diferença que levou à decisão de
trocar o OpenCV pelo PyAV na captura.

**Se um script daqui passar a testar lógica pura, migre para `tests/`.** Foi o que
aconteceu com os dois de atalho: eram parsing de texto e eventos de tecla, não precisavam
de hardware, e enquanto ficaram aqui tiveram zero cobertura automática — incluindo a
regressão do AltGr. Ver D-43.
