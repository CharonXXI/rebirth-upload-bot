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
        'webview.platforms.cocoa',
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
        # Torrent
        'torf',
        # FTP / ruTorrent / SFTP
        'ftplib',
        'ssl',
        'xmlrpc',
        'xmlrpc.client',
        'paramiko',
        'paramiko.transport',
        'paramiko.auth_handler',
        'paramiko.sftp_client',
        # Données / calculs
        'numpy',
        'numpy.core',
        'numpy.core._methods',
        'numpy.lib.format',
        # Affichage terminal
        'rich',
        'rich.console',
        'rich.progress',
        # Stdlib (parfois manquants dans le bundle)
        'uuid',
        'fractions',
        'importlib',
        'importlib.util',
        'hashlib',
        'base64',
        'zipfile',
        'stat',
        'glob',
        'pty',
        # NFO_CUSTOM sous-modules
        'NFO_CUSTOM.NFO_v1_7',
        'NFO_CUSTOM.tmdb_helper',
        'NFO_CUSTOM.source_detector',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
)

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

app = BUNDLE(
    coll,
    name='REBiRTH.app',
    icon=None,
    bundle_identifier='com.rebirth.uploadbot',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '2.9.8',
        'CFBundleName': 'REBiRTH',
        'NSRequiresAquaSystemAppearance': False,
    },
)
