import os
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl


class ChordSoundPlayer:
    def __init__(self):
        self.sounds_base_path = os.path.join("source", "sounds")
        self.media_player = QMediaPlayer()

    def play_chord_sound(self, chord_name, variant=None):
        """Воспроизведение звука аккорда"""
        try:
            # Формируем путь к файлу
            if variant:
                # Если указан вариант, ищем файл вида "A_1.mp3"
                filename = f"{chord_name}_{variant}.mp3"
                file_path = os.path.join(self.sounds_base_path, chord_name, filename)

                # Если файл не найден, пробуем альтернативные варианты именования
                if not os.path.exists(file_path):
                    # Пробуем найти файл с другим форматом имени
                    alt_filename = f"{chord_name}{variant}.mp3"
                    alt_path = os.path.join(self.sounds_base_path, chord_name, alt_filename)
                    if os.path.exists(alt_path):
                        file_path = alt_path
            else:
                # Если вариант не указан, ищем файл с базовым именем
                filename = f"{chord_name}.mp3"
                file_path = os.path.join(self.sounds_base_path, chord_name, filename)

            print(f"🔊 Поиск звукового файла: {file_path}")

            if os.path.exists(file_path):
                # Создаем URL для медиаплеера
                media_url = QUrl.fromLocalFile(file_path)
                media_content = QMediaContent(media_url)

                # Останавливаем предыдущее воспроизведение и запускаем новое
                self.media_player.stop()
                self.media_player.setMedia(media_content)
                self.media_player.play()
                print(f"🎵 Воспроизводится: {os.path.basename(file_path)}")
                return True
            else:
                print(f"❌ Звуковой файл не найден: {file_path}")
                return False

        except Exception as e:
            print(f"❌ Ошибка воспроизведения звука: {e}")
            return False

    def stop_playback(self):
        """Остановка воспроизведения"""
        self.media_player.stop()