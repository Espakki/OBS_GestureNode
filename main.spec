# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# A pasta `ui/qml` PRECISA entrar: os .qml sao lidos do disco em tempo de execucao, nao
# importados como modulo, entao o PyInstaller nao os descobre sozinho. Sem esta linha o
# app empacotado nao encontra a interface e cai no fallback de Widgets -- **em silencio**,
# porque `_construir_aba_geral` trata a falha e segue. Ver D-49.
datas = [('assets', 'assets'), ('ui/qml', 'ui/qml')]
binaries = []
hiddenimports = []

tmp_ret = collect_all('mediapipe')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# --- PyAV / FFmpeg: NAO precisa de nada aqui ---------------------------------
# Verificado no bundle congelado (av==14.2.0, PyInstaller 6.22.2): o hook
# `hook-av.py` do pyinstaller-hooks-contrib ja coleta `av.libs/` inteiro
# (avcodec/avformat/avutil/avdevice/avfilter/swscale/swresample) preservando o
# diretorio, que e o que o patch delvewheel dentro de `av/__init__.py` exige
# para o `os.add_dll_directory`. O demuxer `dshow` usado por core/camera.py
# responde no exe empacotado. Nao adicione collect_all('av') aqui: duplica as
# DLLs no diretorio raiz e quebra o layout que o delvewheel espera.

# --- pygrabber / comtypes: pre-gerar os wrappers de typelib ------------------
# `pygrabber.dshow_core` chama `comtypes.client.GetModule('qedit.dll')` e
# `('quartz.dll')` NO IMPORT. Esses wrappers sao codigo Python GERADO — nao
# existem em tempo de build, sao escritos por comtypes na primeira execucao.
# Congelado, `comtypes/gen` vive dentro do PYZ e nao e gravavel, entao comtypes
# cai para `%TEMP%\comtypes_cache\<exe>-310` e gera tudo la no primeiro boot.
# Isso FUNCIONA (testado), mas depende de %TEMP% gravavel e de gerar+importar
# codigo em runtime — exatamente o que antivirus corporativo bloqueia. E a falha
# seria silenciosa: o import de FilterGraph em ui/mixins/camera_mixin.py esta em
# try/except e viraria None, derrubando so o fallback de listagem de cameras.
#
# Importar pygrabber AQUI, em tempo de build, materializa os wrappers em
# comtypes/gen do venv; o collect_submodules abaixo os congela no bundle e o
# GetModule em runtime resolve tudo por import, sem gerar nada.
try:
    import pygrabber.dshow_core  # noqa: F401  (efeito colateral: popula comtypes.gen)
except Exception as exc:  # pragma: no cover - build-time
    print(f"[main.spec] AVISO: nao foi possivel pre-gerar os wrappers comtypes: {exc}")
    print("[main.spec] O app vai gerar em %TEMP% no primeiro boot (mais fragil).")
hiddenimports += collect_submodules('comtypes.gen')

# --- O que o collect_all('mediapipe') traz de carona e o app não usa -----------
# Medido cortando um por vez, com um bundle console executado a cada passo (B-10):
#   baseline .................. 774 MB
#   sem jax + jaxlib .......... 568 MB
#   sem scipy ................. 480 MB
#
# matplotlib e PIL ficam, apesar de o app não os importar: o mediapipe os carrega
# internamente (drawing_utils), e cortá-los quebra o `Hands()` com ModuleNotFoundError
# — descoberto justamente por cortar em passos e rodar o bundle a cada um. Cortar os
# cinco de uma vez teria publicado um build quebrado.
EXCLUDES = ['jax', 'jaxlib', 'scipy']


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX desligado de proposito. Nunca esteve ligado de fato — o UPX nao esta
    # instalado nesta maquina, entao `upx=True` era um no-op silencioso e nenhum
    # build testado foi comprimido. Numa maquina que tenha o UPX no PATH ele
    # passaria a comprimir Qt/PySide6, as DLLs do FFmpeg e os .pyd do mediapipe,
    # caminho classico de "buildou mas o exe nao abre". Ligue so com teste real.
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='main',
)
