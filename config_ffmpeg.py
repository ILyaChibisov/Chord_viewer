"""
Настройка FFmpeg для Windows
Запустите этот файл если FFmpeg не настроен автоматически
"""

import os
import subprocess
import sys


def setup_ffmpeg():
    """Настраивает FFmpeg в системе"""

    print("🔧 Настройка FFmpeg для Windows")
    print("=" * 40)

    # Проверяем установлен ли Chocolatey
    try:
        result = subprocess.run(['choco', '--version'],
                                capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Chocolatey найден: {result.stdout.strip()}")
        else:
            print("❌ Chocolatey не установлен")
            print("💡 Установите Chocolatey с официального сайта:")
            print("   https://chocolatey.org/install")
            return False
    except:
        print("❌ Chocolatey не установлен")
        return False

    # Устанавливаем FFmpeg через Chocolatey
    print("📥 Установка FFmpeg через Chocolatey...")
    try:
        result = subprocess.run(['choco', 'install', 'ffmpeg', '-y'],
                                capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ FFmpeg успешно установлен")
        else:
            print("❌ Ошибка установки FFmpeg")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False

    # Проверяем установку
    ffmpeg_path = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    if os.path.exists(ffmpeg_path):
        print(f"✅ FFmpeg найден: {ffmpeg_path}")

        # Добавляем в PATH
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
        print("✅ FFmpeg добавлен в PATH")

        return True
    else:
        print("❌ FFmpeg не найден после установки")
        return False


if __name__ == "__main__":
    if setup_ffmpeg():
        print("\n🎉 FFmpeg успешно настроен!")
        print("💡 Теперь запустите конвертер:")
        print("   python run_standalone_converter.py")
    else:
        print("\n❌ Настройка FFmpeg не удалась")
        print("💡 Альтернативные варианты:")
        print("1. Скачайте FFmpeg вручную с https://ffmpeg.org/")
        print("2. Распакуйте в C:\\ffmpeg\\")
        print("3. Добавьте C:\\ffmpeg\\bin\\ в PATH")

    input("\n🎯 Нажмите Enter для выхода...")