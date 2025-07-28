# hooks/hook-numpy.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集numpy的所有子模块
hiddenimports = collect_submodules('numpy')

# 收集numpy的数据文件
datas = collect_data_files('numpy', include_py_files=True)

# 添加特定的numpy 2.x模块
hiddenimports += [
    'numpy._core',
    'numpy._core._exceptions',
    'numpy._core._multiarray_umath',
    'numpy._core._multiarray_tests',
    'numpy._core.multiarray',
    'numpy._core.umath',
    'numpy._core._operand_flag_tests',
    'numpy._core._rational_tests',
    'numpy._core._struct_ufunc_tests',
    'numpy._core._umath_tests',
]