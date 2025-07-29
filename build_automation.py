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
    APP_NAME = "web_setup_automation"
    SPEC_FILE = f"{APP_NAME}.spec"
    DIST_PATH = Path("dist")
    BUILD_PATH = Path("build")

    # 1. 手动输入版本号
    while True:
        version = input("请输入版本号 (例如 0.3.1): ").strip()
        if version:
            break
        print("版本号不能为空，请重新输入。")

    # --- 平台检测 ---
    if sys.platform == "darwin":
        platform_name = "MacOS"
        # 在macOS上，PyInstaller的输出是一个.app目录
        app_bundle_name = f"{APP_NAME}.app"
        archive_source_path = DIST_PATH / app_bundle_name
    elif sys.platform == "win32":
        platform_name = "Windows"
        # 在Windows上，PyInstaller的输出是一个包含exe的目录
        app_bundle_name = APP_NAME
        archive_source_path = DIST_PATH / app_bundle_name
    else:
        platform_name = "Linux"
        app_bundle_name = APP_NAME
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
        "--noconfirm"  # 自动覆盖dist目录
    ]
    
    try:
        result = subprocess.run(pyinstaller_command, check=True, text=True, capture_output=True)
        print("   ✓ PyInstaller 打包成功！")
        # 打印一些输出用于调试
        # print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("   ✗ PyInstaller 打包失败！")
        print("错误信息:")
        print(e.stderr)
        sys.exit(1) # 打包失败，退出脚本
    except FileNotFoundError:
        print("   ✗ 错误: 'pyinstaller' 命令未找到。")
        print("请确保 PyInstaller 已经安装并且在系统的 PATH 路径中。")
        sys.exit(1)

    # 检查打包产物是否存在
    if not archive_source_path.exists():
        print(f"   ✗ 错误: 未在 '{DIST_PATH}' 目录中找到预期的打包产物 '{app_bundle_name}'。")
        print("请检查 PyInstaller 配置和输出。")
        sys.exit(1)

    # 3. 自动打包为 ZIP 文件
    zip_filename_base = f"{platform_name}.{APP_NAME}.{version}"
    print(f"\n📦 正在创建 ZIP 压缩包: {zip_filename_base}.zip ...")

    try:
        # shutil.make_archive需要目标路径和要压缩的目录
        # base_name 是压缩包的文件名（不含扩展名）
        # format 是压缩格式
        # root_dir 是要压缩的文件夹所在的根目录
        # base_dir 是要压缩的文件夹的名称
        shutil.make_archive(
            base_name=zip_filename_base,
            format='zip',
            root_dir=DIST_PATH,
            base_dir=app_bundle_name if sys.platform != "win32" else None # 在Windows上压缩dist目录下的所有内容
        )
        print(f"   ✓ 压缩成功！文件已保存为 '{zip_filename_base}.zip'")
    except Exception as e:
        print(f"   ✗ 压缩失败！")
        print(f"错误信息: {e}")
        sys.exit(1)

    print("\n✨ 所有操作已成功完成！")

if __name__ == "__main__":
    main()
