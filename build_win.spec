# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('gui_index.html', '.'),
        ('NFO_CUSTOM', 'NFO_CUSTOM'),
        ('V1.env', '.'),
        ('gofile.py', '.'),
        ('auto-up-discord.py', '.'),
    ],
    hiddenimports=[
        # GUI
        'webview',
        'webview.platforms.winforms',
        'clr',
        # HTTP / upload
        'requests',
        'requests_toolbelt',
        'tqdm',
        # Config
        'dotenv',
        'python_dotenv',
        # Media
        'pymediainfo',
        # NFO / parsing
        'PTN',
        'parse_torrent_name',
        # Torrent
        'torf',
        # FTP / ruTorrent
        'ftplib',
        'ssl',
        'xmlrpc',
        'xmlrpc.client',
        # Stdlib (parfois manquants dans le bundle)
        'ctypes',
        'ctypes.wintypes',
        'uuid',
        'fractions',
        'importlib',
        'importlib.util',
        # NFO_CUSTOM sous-modules
        'NFO_CUSTOM.NFO_v1_7',
        'NFO_CUSTOM.tmdb_helper',
        'NFO_CUSTOM.source_detector',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='REBiRTH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

# Mode onedir : tous les fichiers dans dist\REBiRTH\
# V1.env est persistant entre les lancements (contrairement au mode onefile)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='REBiRTH',
)
