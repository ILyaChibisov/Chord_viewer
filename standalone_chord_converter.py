import os
import sys
import base64
import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# =============================================================================
# НАСТРОЙКА FFMPEG ДЛЯ PYDUB
# =============================================================================

# Пути к FFmpeg (настройте под вашу систему)
FFMPEG_PATH = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
FFPROBE_PATH = r"C:\ProgramData\chocolatey\bin\ffprobe.exe"

# Проверяем существование FFmpeg
if os.path.exists(FFMPEG_PATH) and os.path.exists(FFPROBE_PATH):
    print(f"✅ FFmpeg найден: {FFMPEG_PATH}")

    # Добавляем в PATH
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']

    # Подавляем warnings от pydub
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")

    HAS_FFMPEG = True
else:
    print(f"⚠️ FFmpeg не найден по пути: {FFMPEG_PATH}")
    print("   Установите FFmpeg: choco install ffmpeg")
    HAS_FFMPEG = False

try:
    import pydub
    from pydub import AudioSegment
    from pydub.effects import compress_dynamic_range, high_pass_filter

    if HAS_FFMPEG:
        # Явно устанавливаем пути для pydub
        pydub.AudioSegment.converter = FFMPEG_PATH
        pydub.AudioSegment.ffprobe = FFPROBE_PATH

        # Переопределяем функцию which для pydub
        import pydub.utils

        original_which = pydub.utils.which


        def custom_which(program):
            if program == "ffmpeg":
                return FFMPEG_PATH
            elif program == "ffprobe":
                return FFPROBE_PATH
            elif program == "avconv":
                return None
            else:
                return original_which(program)


        pydub.utils.which = custom_which

        print("✅ pydub настроен с FFmpeg")
    else:
        print("⚠️ pydub загружен, но FFmpeg не настроен")

    HAS_PYDUB = True

except ImportError:
    HAS_PYDUB = False
    print("⚠️ pydub не установлен. Установите: pip install pydub")
    print("⚠️ Звуки будут сохраняться без оптимизации")


class StandaloneChordConverter:
    """
    Автономный конвертер аккордов - упаковывает ВСЕ данные в один Python файл
    """

    def __init__(self, config_path: str, sounds_base_dir: str = None):
        self.config_path = Path(config_path)
        self.sounds_base_dir = Path(sounds_base_dir) if sounds_base_dir else None
        self.converted_data = {
            'metadata': {
                'converter_version': '2.0',
                'total_chords': 0,
                'template_size': 0,
                'sounds_count': 0,
                'compression_stats': {},
                'ffmpeg_configured': HAS_FFMPEG,
                'pydub_available': HAS_PYDUB
            },
            'template_image': None,
            'original_json_config': None,
            'chords': {}
        }

        self.compression_stats = {
            'chords_processed': 0,
            'sounds_optimized': 0,
            'chords_with_sound': 0,
            'chords_without_sound': 0,
            'original_size': 0,
            'compressed_size': 0
        }

        # Загружаем конфигурацию
        self.config = self.load_configuration()
        if self.config:
            self.load_template_image()

    def load_configuration(self) -> Dict:
        """Загружает JSON-конфигурацию аккордов"""
        try:
            if not self.config_path.exists():
                print(f"❌ Файл конфигурации не существует: {self.config_path}")
                return {}

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            chords_count = len(config.get('chords', {}))
            print(f"✅ Загружена конфигурация: {chords_count} аккордов")

            # Очищаем данные от NaN
            config = self.clean_json_data(config)

            # Сохраняем всю JSON конфигурацию
            self.converted_data['original_json_config'] = config
            self.converted_data['metadata']['original_config_path'] = str(self.config_path)

            return config
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return {}

    def clean_json_data(self, obj):
        """Рекурсивно очищает JSON данные от NaN и недопустимых значений"""
        if isinstance(obj, dict):
            return {k: self.clean_json_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_json_data(item) for item in obj]
        elif isinstance(obj, float) and obj != obj:  # NaN
            return None
        elif obj is None:
            return None
        else:
            return obj

    def load_template_image(self):
        """Загружает основной шаблон изображения в base64"""
        possible_paths = [
            self.config_path.parent / 'img.png',
            self.config_path.parent / 'img.jpg',
            self.config_path.parent / 'template.png',
            Path('img.png'),
            Path('img.jpg'),
            Path('template.png'),
            self.config_path.with_name('img.png'),
        ]

        template_path = None
        for image_path in possible_paths:
            if image_path.exists():
                template_path = image_path
                print(f"🔍 Найден шаблон: {image_path}")
                break

        if not template_path:
            print("❌ Шаблон изображения не найден")
            return

        try:
            with open(template_path, 'rb') as f:
                template_data = f.read()

            template_b64 = base64.b64encode(template_data).decode('utf-8')
            self.converted_data['template_image'] = template_b64
            self.converted_data['metadata']['template_size'] = len(template_data)
            self.converted_data['metadata']['template_path'] = str(template_path)
            print(f"✅ Шаблон изображения сохранен: {len(template_data)} bytes")

        except Exception as e:
            print(f"❌ Ошибка загрузки шаблона: {e}")

    def optimize_audio_file(self, sound_path: Path) -> Optional[bytes]:
        """Оптимизирует аудио файл с реальным сжатием"""
        try:
            original_size = sound_path.stat().st_size

            if not HAS_PYDUB or not HAS_FFMPEG:
                print(f"    ⚠️ pydub/FFmpeg не доступен, сохраняем оригинал: {sound_path.name}")
                with open(sound_path, 'rb') as f:
                    return f.read()

            # Оптимизация с pydub
            return self._optimize_with_pydub(sound_path, original_size)

        except Exception as e:
            print(f"    ❌ Ошибка оптимизации {sound_path.name}: {e}")
            # Возвращаем оригинальный файл в случае ошибки
            with open(sound_path, 'rb') as f:
                return f.read()

    def _optimize_with_pydub(self, sound_path: Path, original_size: int) -> bytes:
        """Оптимизирует аудио с помощью pydub"""
        import io

        try:
            print(f"    🔧 Оптимизация {sound_path.name} с pydub...")

            # Загружаем аудио
            audio_format = sound_path.suffix.lower()[1:]  # убираем точку
            audio = AudioSegment.from_file(sound_path, format=audio_format)
            print(f"    📊 Загружено: {len(audio)} ms, {audio.channels} каналов, {audio.frame_rate} Hz")

            # 1. Обрезаем тишину
            audio = self._remove_silence(audio)
            print(f"    ✂️  После обрезки тишины: {len(audio)} ms")

            # 2. Нормализуем громкость
            audio = self._normalize_volume(audio)
            print(f"    🔊 После нормализации: {audio.dBFS:.1f} dBFS")

            # 3. Компрессия динамического диапазона
            audio = compress_dynamic_range(audio, threshold=-20.0, ratio=2.0)
            print(f"    🎛️  После компрессии: {len(audio)} ms")

            # 4. High-pass фильтр для чистоты звука
            audio = high_pass_filter(audio, cutoff=80)
            print(f"    🎵 После фильтра: {len(audio)} ms")

            # 5. Экспортируем с оптимизацией
            buffer = io.BytesIO()
            audio.export(
                buffer,
                format="mp3",
                bitrate="64k",
                parameters=["-ac", "1", "-ar", "22050"]  # моно, пониженная частота
            )

            compressed_data = buffer.getvalue()
            compressed_size = len(compressed_data)

            # Обновляем статистику
            self.compression_stats['original_size'] += original_size
            self.compression_stats['compressed_size'] += compressed_size
            self.compression_stats['sounds_optimized'] += 1

            compression_ratio = (original_size - compressed_size) / original_size * 100
            print(
                f"    ✅ {sound_path.name}: {original_size / 1024:.1f}KB → {compressed_size / 1024:.1f}KB ({compression_ratio:+.1f}%)")

            return compressed_data

        except Exception as e:
            print(f"    ❌ Ошибка pydub оптимизации: {e}")
            import traceback
            traceback.print_exc()
            # Возвращаем оригинальный файл
            with open(sound_path, 'rb') as f:
                return f.read()

    def _remove_silence(self, audio, silence_thresh=-40.0):
        """Обрезает тишину в начале и конце"""
        try:
            print(f"    🔇 Поиск тишины...")
            non_silent = audio.detect_silence(
                silence_thresh=silence_thresh,
                min_silence_len=100,
                seek_step=10
            )

            if not non_silent:
                print(f"    🔇 Тишина не найдена")
                return audio

            start = max(0, non_silent[0][0] - 50)
            end = min(len(audio), non_silent[-1][1] + 100)

            print(f"    ✂️  Обрезка: {len(audio)}ms → {end - start}ms")
            return audio[start:end]
        except Exception as e:
            print(f"    ⚠️ Ошибка обрезки тишины: {e}")
            return audio

    def _normalize_volume(self, audio, target_dBFS=-16.0):
        """Нормализует громкость"""
        try:
            current_dBFS = audio.dBFS
            change_in_dBFS = target_dBFS - current_dBFS
            print(f"    🔊 Нормализация: {current_dBFS:.1f}dBFS → {target_dBFS:.1f}dBFS")
            return audio.apply_gain(change_in_dBFS)
        except Exception as e:
            print(f"    ⚠️ Ошибка нормализации громкости: {e}")
            return audio

    def find_sound_files_for_chord(self, chord_name: str) -> List[Path]:
        """Находит звуковые файлы для аккорда"""
        if not self.sounds_base_dir or not self.sounds_base_dir.exists():
            return []

        safe_name = self.get_safe_chord_name(chord_name)
        chord_dir = self.sounds_base_dir / safe_name

        if not chord_dir.exists():
            # Пробуем найти по базовому имени (без цифр)
            base_name = self.get_base_chord_name(chord_name)
            if base_name != safe_name:
                chord_dir = self.sounds_base_dir / base_name

        if not chord_dir.exists():
            return []

        # Ищем аудио файлы
        sound_files = []
        for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            found_files = list(chord_dir.glob(f'*{ext}'))
            sound_files.extend(found_files)
            if found_files:
                print(f"    🔍 Найдено {len(found_files)} файлов {ext}")

        return sorted(sound_files)

    def get_safe_chord_name(self, chord_name: str) -> str:
        """Создает безопасное имя для папки"""
        replacements = {
            '/': '_slash_',
            '#': '_sharp_',
            '\\': '_',
            ' ': '_'
        }
        safe_name = chord_name
        for old, new in replacements.items():
            safe_name = safe_name.replace(old, new)
        return safe_name

    def get_base_chord_name(self, chord_name: str) -> str:
        """Извлекает базовое имя аккорда (без цифр)"""
        import re
        # Убираем цифры в конце
        base_name = re.sub(r'\d+$', '', chord_name)
        return self.get_safe_chord_name(base_name)

    def process_all_chords(self):
        """Обрабатывает все аккорды из конфигурации"""
        if not self.config:
            print("❌ Конфигурация не загружена")
            return

        chords_data = self.config.get('chords', {})
        print(f"🔧 Обработка {len(chords_data)} аккордов...")

        for chord_key, chord_data in chords_data.items():
            print(f"  🎵 {chord_key}")

            # Извлекаем информацию об аккорде
            base_info = chord_data.get('base_info', {})
            chord_name = base_info.get('base_chord', chord_key)
            group_name = chord_data.get('group', 'unknown')

            # Ищем звуковые файлы
            sound_files = self.find_sound_files_for_chord(chord_name)
            variants = []

            # Создаем варианты аккорда
            for i, sound_file in enumerate(sound_files, 1):
                print(f"    🎵 Обработка варианта {i}: {sound_file.name}")

                # Оптимизируем звук
                sound_data = self.optimize_audio_file(sound_file)
                sound_b64 = base64.b64encode(sound_data).decode() if sound_data else None

                # Создаем вариант с JSON параметрами
                variant = {
                    'position': i,
                    'description': f"Вариант {i}",
                    'json_parameters': {
                        'crop_rect': chord_data.get('crop_rect', []),
                        'elements_fingers': chord_data.get('elements_fingers', []),
                        'elements_notes': chord_data.get('elements_notes', []),
                        'display_settings': chord_data.get('display_settings', {})
                    },
                    'sound_data': sound_b64
                }
                variants.append(variant)

            # Если нет звуков, создаем базовый вариант
            if not variants:
                variants.append({
                    'position': 1,
                    'description': "Основной вариант",
                    'json_parameters': {
                        'crop_rect': chord_data.get('crop_rect', []),
                        'elements_fingers': chord_data.get('elements_fingers', []),
                        'elements_notes': chord_data.get('elements_notes', []),
                        'display_settings': chord_data.get('display_settings', {})
                    },
                    'sound_data': None
                })

            # Сохраняем аккорд
            self.converted_data['chords'][chord_name] = {
                'name': chord_name,
                'group': group_name,
                'description': base_info.get('caption', f'Аккорд {chord_name}'),
                'type': base_info.get('type', 'major').lower(),
                'variants': variants
            }

            # Обновляем статистику
            self.compression_stats['chords_processed'] += 1
            if any(v['sound_data'] for v in variants):
                self.compression_stats['chords_with_sound'] += 1
            else:
                self.compression_stats['chords_without_sound'] += 1

            print(f"    ✅ {len(variants)} вариантов")

    def save_as_python_file(self, output_path: str = "chords_data.py"):
        """Сохраняет все данные в один Python файл"""
        print(f"💾 Сохранение в {output_path}...")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            # Заголовок файла
            f.write('''"""
АВТОНОМНЫЕ ДАННЫЕ АККОРДОВ
Генератор: StandaloneChordConverter
ВСЕ данные для работы приложения в одном файле
"""

import base64
import json
from typing import Dict, List, Optional

# Основные данные аккордов
CHORDS_DATA = {
''')

            # Метаданные
            f.write('    "metadata": {\n')
            metadata = self.converted_data['metadata'].copy()
            metadata.update({
                'total_chords': len(self.converted_data['chords']),
                'chords_with_sound': self.compression_stats['chords_with_sound'],
                'chords_without_sound': self.compression_stats['chords_without_sound'],
                'sounds_optimized': self.compression_stats['sounds_optimized'],
                'compression_ratio': f"{(self.compression_stats['original_size'] - self.compression_stats['compressed_size']) / self.compression_stats['original_size'] * 100:.1f}%" if
                self.compression_stats['original_size'] > 0 else "0%"
            })

            for key, value in metadata.items():
                if isinstance(value, str):
                    f.write(f'        "{key}": "{value}",\n')
                else:
                    f.write(f'        "{key}": {value},\n')
            f.write('    },\n')

            # Шаблон изображения
            f.write('    "template_image": """\\\n')
            if self.converted_data['template_image']:
                f.write(self.converted_data['template_image'])
            f.write('""",\n\n')

            # Оригинальная JSON конфигурация
            f.write('    "original_json_config": ')
            json_str = json.dumps(self.converted_data['original_json_config'],
                                  ensure_ascii=False, indent=4)
            # Заменяем null на None для Python
            json_str = json_str.replace(': null', ': None')
            f.write(json_str)
            f.write(',\n\n')

            # Данные аккордов
            f.write('    "chords": {\n')

            for i, (chord_name, chord_data) in enumerate(self.converted_data['chords'].items()):
                f.write(f'        "{chord_name}": {{\n')
                f.write(f'            "name": "{chord_data["name"]}",\n')
                f.write(f'            "group": "{chord_data["group"]}",\n')
                f.write(f'            "description": "{chord_data["description"]}",\n')
                f.write(f'            "type": "{chord_data["type"]}",\n')
                f.write(f'            "variants": [\n')

                for variant in chord_data['variants']:
                    f.write('                {\n')
                    f.write(f'                    "position": {variant["position"]},\n')
                    f.write(f'                    "description": "{variant["description"]}",\n')

                    # JSON параметры
                    f.write('                    "json_parameters": {\n')
                    params = variant['json_parameters']
                    f.write(f'                        "crop_rect": {json.dumps(params["crop_rect"])},\n')
                    f.write(
                        f'                        "elements_fingers": {json.dumps(params["elements_fingers"], ensure_ascii=False)},\n')
                    f.write(
                        f'                        "elements_notes": {json.dumps(params["elements_notes"], ensure_ascii=False)},\n')
                    f.write(f'                        "display_settings": {json.dumps(params["display_settings"])}\n')
                    f.write('                    },\n')

                    # Звуковые данные
                    if variant['sound_data']:
                        f.write(f'                    "sound_data": """{variant["sound_data"]}"""\n')
                    else:
                        f.write(f'                    "sound_data": None\n')

                    f.write('                },\n')

                f.write('            ]\n')
                f.write('        }')

                # Запятая для всех кроме последнего
                if i < len(self.converted_data['chords']) - 1:
                    f.write(',')
                f.write('\n')

            f.write('    }\n')
            f.write('}\n\n')

            # Вспомогательные функции для загрузки данных
            f.write('''
def get_template_image() -> bytes:
    """Возвращает шаблон изображения как bytes"""
    if CHORDS_DATA["template_image"]:
        return base64.b64decode(CHORDS_DATA["template_image"])
    return None

def get_chord_config(chord_name: str) -> Optional[Dict]:
    """Возвращает конфигурацию аккорда по имени"""
    return CHORDS_DATA["chords"].get(chord_name)

def get_all_chords() -> List[str]:
    """Возвращает список всех доступных аккордов"""
    return list(CHORDS_DATA["chords"].keys())

def get_chord_sound(chord_name: str, variant: int = 1) -> Optional[bytes]:
    """Возвращает звук аккорда для указанного варианта"""
    chord_data = CHORDS_DATA["chords"].get(chord_name)
    if not chord_data:
        return None

    for variant_data in chord_data['variants']:
        if variant_data['position'] == variant and variant_data['sound_data']:
            return base64.b64decode(variant_data['sound_data'])

    return None

def get_original_config() -> Dict:
    """Возвращает оригинальную JSON конфигурацию"""
    return CHORDS_DATA["original_json_config"]

def get_metadata() -> Dict:
    """Возвращает метаданные"""
    return CHORDS_DATA["metadata"]

if __name__ == "__main__":
    print("📊 Статистика данных аккордов:")
    metadata = get_metadata()
    print(f"🎸 Аккордов: {len(get_all_chords())}")
    print(f"🖼️  Размер шаблона: {metadata.get('template_size', 0) / 1024:.1f} KB")
    print(f"🔊 Звуков: {metadata.get('sounds_optimized', 0)}")
    print(f"⚙️  FFmpeg: {'✅ настроен' if metadata.get('ffmpeg_configured') else '❌ не настроен'}")
    print(f"🔧 pydub: {'✅ доступен' if metadata.get('pydub_available') else '❌ не доступен'}")
    print(f"📦 Версия: {metadata.get('converter_version', 'unknown')}")
''')

        print(f"✅ Файл сохранен: {output_file}")

    def print_statistics(self):
        """Выводит подробную статистику"""
        print(f"\n📊 ДЕТАЛЬНАЯ СТАТИСТИКА:")
        print(f"   🎸 Обработано аккордов: {self.compression_stats['chords_processed']}")
        print(f"   🔊 Со звуком: {self.compression_stats['chords_with_sound']}")
        print(f"   🔇 Без звука: {self.compression_stats['chords_without_sound']}")
        print(f"   ⚙️  FFmpeg: {'✅ настроен' if HAS_FFMPEG else '❌ не настроен'}")
        print(f"   🔧 pydub: {'✅ доступен' if HAS_PYDUB else '❌ не доступен'}")

        if self.converted_data['template_image']:
            template_size = len(base64.b64decode(self.converted_data['template_image']))
            print(f"   🖼️  Шаблон изображения: {template_size / 1024:.1f} KB")

        if self.compression_stats['sounds_optimized'] > 0:
            total_savings = self.compression_stats['original_size'] - self.compression_stats['compressed_size']
            savings_percent = (total_savings / self.compression_stats['original_size'] * 100) if self.compression_stats[
                                                                                                     'original_size'] > 0 else 0

            print(f"   💾 Экономия места на звуках: {total_savings / 1024 / 1024:.2f} MB ({savings_percent:+.1f}%)")
            print(f"   📦 Исходный размер звуков: {self.compression_stats['original_size'] / 1024 / 1024:.2f} MB")
            print(f"   📦 Сжатый размер звуков: {self.compression_stats['compressed_size'] / 1024 / 1024:.2f} MB")


def find_config_file() -> Optional[Path]:
    """Автоматически находит файл конфигурации"""
    possible_paths = [
        Path("chords_configuration.json"),
        Path("chords_config/chords_configuration.json"),
        Path("templates2/chords_configuration.json"),
        Path("config/chords_configuration.json"),
        Path("../chords_configuration.json"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✅ Найден файл конфигурации: {path}")
            return path

    print("❌ Файл конфигурации не найден")
    return None


def find_sounds_directory() -> Optional[Path]:
    """Автоматически находит папку со звуками"""
    possible_paths = [
        Path("sounds"),
        Path("sound"),
        Path("chords_config/sounds"),
        Path("templates2/sounds"),
        Path("../sounds"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✅ Найдена папка со звуками: {path}")
            return path

    print("⚠️ Папка со звуками не найдена")
    return None


def main():
    """Основная функция конвертера"""
    print("🎸 STANDALONE CHORD CONVERTER")
    print("=" * 50)
    print("Упаковывает ВСЕ данные аккордов в один Python файл")
    print(f"⚙️  FFmpeg: {'✅ настроен' if HAS_FFMPEG else '❌ не настроен'}")
    print(f"🔧 pydub: {'✅ доступен' if HAS_PYDUB else '❌ не доступен'}")

    # Автопоиск файлов
    config_path = find_config_file()
    if not config_path:
        return

    sounds_dir = find_sounds_directory()

    # Создаем и запускаем конвертер
    converter = StandaloneChordConverter(config_path, sounds_dir)
    converter.process_all_chords()
    converter.save_as_python_file("chords_data.py")
    converter.print_statistics()

    print(f"\n✅ ГОТОВО! Все данные сохранены в chords_data.py")
    print("💡 Теперь приложение может работать полностью автономно!")


if __name__ == "__main__":
    main()