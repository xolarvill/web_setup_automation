import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """
    自动化构建、打包和压缩脚本。
    """
    # --- 基本配置 ---
    # 应用的显示名称，用于最终的ZIP文件名
    APP_DISPLAY_NAME = "Web Setup Automation"
    # PyInstaller的spec文件名和在Windows/Linux上的输出目录名
    PYINSTALLER_OUTPUT_NAME = "web_setup_automation"
    SPEC_FILE = f"{PYINSTALLER_OUTPUT_NAME}.spec"
    DIST_PATH = Path("dist")
    BUILD_PATH = Path("build")

    # 1. 手动输入版本号
    while True:
        version = input(f"请输入 '{APP_DISPLAY_NAME}' 的版本号 (例如 0.3.1): ").strip()
        if version:
            break
        print("版本号不能为空，请重新输入。")

    # --- 平台检测和路径配置 ---
    if sys.platform == "darwin":
        platform_name = "MacOS"
        # 在macOS上，PyInstaller的输出是一个.app目录，其名称在spec文件中定义
        app_bundle_name = f"{APP_DISPLAY_NAME}.app"
    elif sys.platform == "win32":
        platform_name = "Windows"
        # 在Windows上，PyInstaller的输出是一个与spec文件名同名的目录
        app_bundle_name = f"{APP_DISPLAY_NAME}.exe"
    else:
        platform_name = "Linux"
        app_bundle_name = PYINSTALLER_OUTPUT_NAME
    
    archive_source_path = DIST_PATH / app_bundle_name

    # --- 清理旧的构建文件 ---
    print("🧹 正在清理旧的构建目录...")
    if DIST_PATH.exists():
        shutil.rmtree(DIST_PATH)
        print(f"   ✓ 已删除 '{DIST_PATH}'")
    if BUILD_PATH.exists():
        shutil.rmtree(BUILD_PATH)
        print(f"   ✓ 已删除 '{BUILD_PATH}'")

    # 2. 使用 PyInstaller 打包
    print(f"\n🔨 正在使用 PyInstaller 打包应用 (版本: {version})...")
    pyinstaller_command = [
        "pyinstaller",
        SPEC_FILE,
        "--noconfirm"
    ]
    
    try:
        result = subprocess.run(pyinstaller_command, check=True, text=True, capture_output=True)
        print("   ✓ PyInstaller 打包成功！")
    except subprocess.CalledProcessError as e:
        print("   ✗ PyInstaller 打包失败！")
        print("错误信息:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("   ✗ 错误: 'pyinstaller' 命令未找到。")
        print("请确保 PyInstaller 已经安装并且在系统的 PATH 路径中。")
        sys.exit(1)

    # 检查打包产物是否存在
    if not archive_source_path.exists():
        print(f"   ✗ 错误: 未在 '{DIST_PATH}' 目录中找到预期的打包产物 '{app_bundle_name}'。")
        print("请检查 PyInstaller spec 文件中的 'name' 配置是否正确。")
        sys.exit(1)

    # 3. 自动打包为 ZIP 文件并放入 dist 文件夹
    zip_display_name = APP_DISPLAY_NAME.replace(" ","_")
    zip_filename_base = f"{platform_name}.{zip_display_name}.{version}"
    # 将输出路径（base_name）设置为 dist 目录内
    zip_output_path = DIST_PATH / zip_filename_base
    
    print(f"\n📦 正在创建 ZIP 压缩包: {zip_filename_base}.zip ...")

    try:
        shutil.make_archive(
            base_name=str(zip_output_path),
            format='zip',
            root_dir=DIST_PATH,
            base_dir=app_bundle_name
        )
        print(f"   ✓ 压缩成功！文件已保存到 '{DIST_PATH}' 目录中。")
    except Exception as e:
        print(f"   ✗ 压缩失败！")
        print(f"错误信息: {e}")
        sys.exit(1)

    print(f"\n✨ 所有操作已成功完成！打包文件位于: {DIST_PATH}")

if __name__ == "__main__":
    main()