import os
import re


def rename_chord_files_simple(directory_path):
    """
    Упрощенная версия для прямого указания пути
    """
    for folder_name in os.listdir(directory_path):
        folder_path = os.path.join(directory_path, folder_name)

        if not os.path.isdir(folder_path):
            continue

        print(f"Обрабатываю папку: {folder_name}")

        file_counter = 1
        mp3_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
        mp3_files.sort()

        for filename in mp3_files:
            file_path = os.path.join(folder_path, filename)
            name_without_ext = os.path.splitext(filename)[0]

            if name_without_ext == folder_name:
                new_name = f"{folder_name}_1.mp3"
            else:
                match = re.search(r'\(.*?(\d+).*?\)', name_without_ext)
                if match:
                    variant_number = match.group(1)
                    new_name = f"{folder_name}_{variant_number}.mp3"
                else:
                    new_name = f"{folder_name}_{file_counter}.mp3"

            new_path = os.path.join(folder_path, new_name)

            try:
                os.rename(file_path, new_path)
                print(f"  '{filename}' -> '{new_name}'")
            except OSError as e:
                print(f"  Ошибка: {e}")

            file_counter += 1

        print()


# Использование
if __name__ == "__main__":
    path = "source/sounds"  # укажите ваш путь здесь
    rename_chord_files_simple(path)