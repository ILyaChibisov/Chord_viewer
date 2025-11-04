#!/usr/bin/env python3
"""
Запускатель автономного конвертера аккордов
"""

import os
import sys
from pathlib import Path


def main():
    print("🎸 Запуск автономного конвертера аккордов")
    print("=" * 50)

    # Добавляем текущую директорию в путь
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))

    try:
        from standalone_chord_converter import main as converter_main
        converter_main()

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\n🔧 Решение: установите зависимости:")
        print("pip install pydub")
        print("choco install ffmpeg  # или скачайте вручную")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    input("\n🎯 Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()