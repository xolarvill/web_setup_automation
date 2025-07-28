# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# --- Platform-specific setup ---
if sys.platform.startswith('win32'):
    icon_file = 'resources/icon.ico'
elif sys.platform.startswith('darwin'):
    icon_file = 'resources/icon.icns'
else:
    icon_file = 'resources/icon.png'

# Verify icon file exists
if not os.path.exists(icon_file):
    print(f"Warning: Icon file {icon_file} not found!")
    icon_file = None

# --- Analysis Block ---
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('temps', 'temps'),
        ('ui', 'ui'),
        ('utils', 'utils'),
        ('miscellaneous', 'miscellaneous'),
        ('size.csv', '.'),
        ('aws_config.json', '.')
    ],
    hiddenimports=[
        # --- PySide6 相关 ---
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'qt_material',
        
        # --- Keyring 相关 ---
        'keyring.backends',
        'keyring.backends.macOS',
        'keyring.backends.SecretService', 
        'keyring.backends.Windows',
        
        # --- NumPy 和 Pandas 相关（关键修复）---
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.linalg._umath_linalg',
        'numpy.random._common',
        'numpy.random.bit_generator',
        'numpy.random._generator',
        'numpy.random._mt19937',
        'numpy.random.mtrand',
        'numpy.random._philox',
        'numpy.random._pcg64',
        'numpy.random._sfc64',
        'pandas',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.skiplist',
        'pandas.io.formats.format',
        'pandas.io.common',
        'pandas.io.parsers.readers',
        'pandas._libs.parsers',
        'pandas._libs.tslibs.strptime',
        
        # --- Selenium 和 WebDriver 相关 ---
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        'webdriver_manager',
        'webdriver_manager.chrome',
        
        # --- 网络和请求相关 ---
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.exceptions',
        'urllib3',
        'urllib3.util.retry',
        
        # --- AWS 相关 ---
        'boto3',
        'botocore',
        'botocore.client',
        'botocore.exceptions',
        
        # --- 打包工具相关 ---
        'pkg_resources.py2_warn',
        'packaging.version',
        'packaging.specifiers', 
        'packaging.requirements',
        
        # --- 其他依赖 ---
        'charset_normalizer',
        'certifi',
        'idna',
    ],
    hookspath=[],
    hooksconfig={
        # 特别配置pandas和numpy的hook
        'pandas': {
            'include_pandas_datareader': False,
        }
    },
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.tests',
        'numpy.tests',
        'pandas.tests',
        'scipy.tests',
        'IPython',
        'jupyter',
        'notebook',
        # 排除一些可能冲突的测试模块
        'pandas.util.testing',
        'numpy.testing',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# --- PYZ Block ---
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --- EXE Block ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='web_setup_automation',
    debug=False,  # 可以临时设为True进行调试
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩，numpy/pandas经常与UPX有兼容问题
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 调试时可以改为True
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if icon_file else None
)

# --- macOS App Bundle ---
if sys.platform.startswith('darwin'):
    app_bundle = BUNDLE(
        exe,
        name='web_setup_automation.app',
        icon=icon_file if icon_file else None,
        bundle_identifier='com.victorli.websetupautomation',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': 'Web Setup Automation',
            'CFBundleName': 'Web Setup Automation',
            'CFBundleShortVersionString': '0.1.63',
            'CFBundleVersion': '0.1.63',
            'LSMinimumSystemVersion': '10.13.0',
            'NSRequiresAquaSystemAppearance': False,
        }
    )

# --- Windows/Linux Distribution ---
if not sys.platform.startswith('darwin'):
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,  # 同样禁用UPX
        upx_exclude=[],
        name='web_setup_automation'
    )