"""
Загрузчик данных из chords_data.py для основного приложения
"""

import base64
import json
from typing import Dict, List, Optional, Tuple

try:
    from chords_data import CHORDS_DATA, get_template_image, get_chord_config, get_all_chords, get_chord_sound
    HAS_CHORDS_DATA = True
except ImportError:
    HAS_CHORDS_DATA = False
    print("⚠️ chords_data.py не найден, запустите конвертер сначала")

class ChordsDataLoader:
    """
    Загружает все данные из автономного файла chords_data.py
    """

    def __init__(self):
        if not HAS_CHORDS_DATA:
            raise ImportError("Файл chords_data.py не найден")

        self.metadata = CHORDS_DATA.get('metadata', {})
        self.template_image = None
        self.original_config = CHORDS_DATA.get('original_json_config', {})
        self.chords_data = CHORDS_DATA.get('chords', {})

        # Загружаем шаблон изображения
        self._load_template_image()

    def _load_template_image(self):
        """Загружает шаблон изображения из base64"""
        template_b64 = CHORDS_DATA.get('template_image')
        if template_b64:
            self.template_image = base64.b64decode(template_b64)

    def get_template_image_data(self) -> Optional[bytes]:
        """Возвращает данные шаблонного изображения"""
        return self.template_image

    def get_chord_names(self) -> List[str]:
        """Возвращает список всех доступных аккордов"""
        return list(self.chords_data.keys())

    def get_chord_data(self, chord_name: str) -> Optional[Dict]:
        """Возвращает полные данные аккорда"""
        return self.chords_data.get(chord_name)

    def get_chord_variants(self, chord_name: str) -> List[Dict]:
        """Возвращает варианты аккорда"""
        chord_data = self.get_chord_data(chord_name)
        return chord_data.get('variants', []) if chord_data else []

    def get_chord_sound_data(self, chord_name: str, variant: int = 1) -> Optional[bytes]:
        """Возвращает звуковые данные аккорда"""
        variants = self.get_chord_variants(chord_name)
        for var in variants:
            if var.get('position') == variant and var.get('sound_data'):
                return base64.b64decode(var['sound_data'])
        return None

    def get_chord_json_parameters(self, chord_name: str, variant: int = 1) -> Optional[Dict]:
        """Возвращает JSON параметры для отрисовки аккорда"""
        variants = self.get_chord_variants(chord_name)
        for var in variants:
            if var.get('position') == variant:
                return var.get('json_parameters', {})
        return None

    def get_original_config(self) -> Dict:
        """Возвращает оригинальную JSON конфигурацию"""
        return self.original_config

    def get_metadata(self) -> Dict:
        """Возвращает метаданные"""
        return self.metadata

    def print_stats(self):
        """Выводит статистику загруженных данных"""
        print("📊 ДАННЫЕ ИЗ chords_data.py:")
        print(f"🎸 Аккордов: {len(self.get_chord_names())}")
        print(f"🖼️  Шаблон: {'✅ загружен' if self.template_image else '❌ отсутствует'}")
        print(f"📋 Конфигурация: {'✅ загружена' if self.original_config else '❌ отсутствует'}")
        print(f"🔊 Звуков: {self.metadata.get('sounds_optimized', 0)}")
        print(f"⚙️  FFmpeg: {'✅ настроен' if self.metadata.get('ffmpeg_configured') else '❌ не настроен'}")
        print(f"🔧 pydub: {'✅ доступен' if self.metadata.get('pydub_available') else '❌ не доступен'}")

# Пример использования в основном приложении
if __name__ == "__main__":
    try:
        loader = ChordsDataLoader()
        loader.print_stats()

        # Пример получения данных аккорда
        chords = loader.get_chord_names()
        if chords:
            sample_chord = chords[0]
            print(f"\n🎵 Пример аккорда '{sample_chord}':")
            chord_data = loader.get_chord_data(sample_chord)
            print(f"   Описание: {chord_data.get('description')}")
            print(f"   Вариантов: {len(chord_data.get('variants', []))}")

    except ImportError as e:
        print("❌ Сначала запустите конвертер для создания chords_data.py")