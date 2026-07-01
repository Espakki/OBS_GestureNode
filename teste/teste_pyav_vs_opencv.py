"""
Benchmark: PyAV vs OpenCV CAP_DSHOW — pipeline completo com MediaPipe
Mede latencia frame-a-frame: captura -> decode -> MediaPipe Hands inference

Uso:
    python teste/teste_pyav_vs_opencv.py                  # roda benchmark
    python teste/teste_pyav_vs_opencv.py --list-cameras   # lista cameras DirectShow disponiveis

Dependencias adicionais (nao esta no requirements.txt):
    pip install av
"""
import sys
import time
import numpy as np
import cv2
import mediapipe as mp

# ── Configuracao ──────────────────────────────────────────────────────────────
CAMERA_INDEX = 0                           # indice para OpenCV
CAMERA_NAME  = "Integrated Camera"        # nome exato para PyAV/DirectShow
                                           # ajuste conforme Gerenciador de Dispositivos > Cameras
RESOLUCAO_W  = 1280
RESOLUCAO_H  = 720
FPS_ALVO     = 30
N_FRAMES     = 200                         # frames por pipeline (~6-7s a 30fps)
# ─────────────────────────────────────────────────────────────────────────────


def listar_cameras_dshow() -> None:
    """Lista dispositivos DirectShow disponiveis via PyAV/FFmpeg."""
    try:
        import av
        # FFmpeg imprime a lista de devices ao stderr quando recebe um device invalido
        # O erro esperado contem os nomes dos dispositivos
        av.open('video=__listar__', format='dshow', options={'list_devices': 'true'})
    except Exception as e:
        print("Dispositivos de video disponiveis:")
        for linha in str(e).splitlines():
            if 'video' in linha.lower() or '@device' in linha.lower() or '"' in linha:
                print(f"  {linha.strip()}")


def resumo(nome: str, latencias: list[float]) -> None:
    arr = np.array(latencias)
    fps = 1000.0 / arr.mean()
    print(f"\n{'─' * 52}")
    print(f"  {nome}")
    print(f"{'─' * 52}")
    print(f"  Frames capturados  : {len(arr)}")
    print(f"  Latencia media     : {arr.mean():.1f} ms")
    print(f"  Latencia mediana   : {np.median(arr):.1f} ms")
    print(f"  P95                : {np.percentile(arr, 95):.1f} ms")
    print(f"  Min / Max          : {arr.min():.1f} / {arr.max():.1f} ms")
    print(f"  FPS efetivo        : {fps:.1f}")


def benchmark_opencv(hands) -> list[float]:
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  RESOLUCAO_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCAO_H)
    cap.set(cv2.CAP_PROP_FPS,          FPS_ALVO)
    # Setar FOURCC duas vezes e necessario no Windows para MJPEG pegar de fato
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    # Descarta frames do buffer de inicializacao
    for _ in range(10):
        cap.read()

    latencias = []
    for _ in range(N_FRAMES):
        t0 = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hands.process(frame_rgb)
        latencias.append((time.perf_counter() - t0) * 1000)

    cap.release()
    return latencias


def benchmark_pyav(hands, hwaccel: str | None = None) -> list[float]:
    import av

    options = {
        'video_size': f'{RESOLUCAO_W}x{RESOLUCAO_H}',
        'framerate': str(FPS_ALVO),
        'vcodec': 'mjpeg',
    }
    if hwaccel:
        options['hwaccel'] = hwaccel

    container = av.open(f'video={CAMERA_NAME}', format='dshow', options=options)
    video = next(s for s in container.streams if s.type == 'video')

    # Descarta frames iniciais
    descartados = 0
    for packet in container.demux(video):
        for _ in packet.decode():
            descartados += 1
        if descartados >= 10:
            break

    latencias = []
    count = 0
    for packet in container.demux(video):
        t0 = time.perf_counter()
        for frame in packet.decode():
            arr = frame.to_ndarray(format='rgb24')
            hands.process(arr)
            latencias.append((time.perf_counter() - t0) * 1000)
            count += 1
        if count >= N_FRAMES:
            break

    container.close()
    return latencias


if __name__ == '__main__':
    if '--list-cameras' in sys.argv:
        listar_cameras_dshow()
        sys.exit(0)

    try:
        import av  # noqa: F401
    except ImportError:
        print("PyAV nao instalado. Execute: pip install av")
        print("(O benchmark OpenCV ainda sera executado)\n")

    mp_hands_cfg = mp.solutions.hands
    hands_kwargs = dict(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    print(f"Benchmark: {N_FRAMES} frames | {RESOLUCAO_W}x{RESOLUCAO_H} @ {FPS_ALVO}fps")
    print(f"Camera OpenCV : indice {CAMERA_INDEX}")
    print(f"Camera PyAV   : '{CAMERA_NAME}'")
    print(f"(edite CAMERA_NAME no topo do arquivo se necessario)")

    # ── [1/3] OpenCV baseline ─────────────────────────────────────────────────
    print("\n[1/3] OpenCV + CAP_DSHOW + MJPEG...")
    with mp_hands_cfg.Hands(**hands_kwargs) as hands:
        lat_opencv = benchmark_opencv(hands)

    # ── [2/3] PyAV CPU ───────────────────────────────────────────────────────
    print("[2/3] PyAV + DirectShow (CPU decode)...")
    lat_pyav_cpu = None
    try:
        with mp_hands_cfg.Hands(**hands_kwargs) as hands:
            lat_pyav_cpu = benchmark_pyav(hands)
    except Exception as e:
        print(f"  FALHOU: {e}")
        print(f"  Dica: verifique se CAMERA_NAME esta correto. Use --list-cameras")

    # ── [3/3] PyAV + dxva2 ───────────────────────────────────────────────────
    print("[3/3] PyAV + DirectShow + dxva2 (hardware decode)...")
    lat_pyav_hw = None
    try:
        with mp_hands_cfg.Hands(**hands_kwargs) as hands:
            lat_pyav_hw = benchmark_pyav(hands, hwaccel='dxva2')
    except Exception as e:
        print(f"  FALHOU (GPU pode nao suportar dxva2 para MJPEG): {e}")

    # ── Resultados ────────────────────────────────────────────────────────────
    print("\n\n══ RESULTADOS ══════════════════════════════════════")
    resumo("OpenCV CAP_DSHOW + MJPEG", lat_opencv)
    if lat_pyav_cpu is not None:
        resumo("PyAV DirectShow — CPU decode", lat_pyav_cpu)
    else:
        print("\n  PyAV (CPU): nao disponivel")
    if lat_pyav_hw is not None:
        resumo("PyAV DirectShow — dxva2 hardware", lat_pyav_hw)
    else:
        print("  PyAV (HW):  nao disponivel")

    print("\n" + "═" * 52)
