"""
ОБНОВЛЕННОЕ ОСНОВНОЕ ПРИЛОЖЕНИЕ
Работает с автономными данными из chords_data.py
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QComboBox, QLabel, QScrollArea, QGridLayout,
                             QGroupBox, QMessageBox, QSizePolicy, QFileDialog, QMainWindow, QApplication, QToolBar,
                             QAction)
from PyQt5.QtCore import Qt, QSize, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
import os
import json
import sys

# Импортируем наш загрузчик автономных данных
try:
    from chords_data_loader import ChordsDataLoader

    HAS_STANDALONE_DATA = True
except ImportError:
    HAS_STANDALONE_DATA = False
    print("⚠️ chords_data_loader не найден")

from drawing_elements import DrawingElements
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QBuffer


class StandaloneChordSoundPlayer:
    """Плеер звуков для автономных данных"""

    def __init__(self, chords_loader):
        self.chords_loader = chords_loader
        self.media_player = QMediaPlayer()

    def play_chord_sound(self, chord_name, variant=1):
        """Воспроизведение звука аккорда из автономных данных"""
        try:
            # Получаем звуковые данные
            sound_data = self.chords_loader.get_chord_sound_data(chord_name, variant)

            if not sound_data:
                print(f"❌ Звук не найден для {chord_name}, вариант {variant}")
                return False

            # Создаем временный буфер для медиаплеера
            buffer = QBuffer()
            buffer.setData(sound_data)
            buffer.open(QBuffer.ReadOnly)

            # Создаем медиаконтент
            media_content = QMediaContent()

            # Останавливаем предыдущее воспроизведение
            self.media_player.stop()

            # Устанавливаем медиа и воспроизводим
            self.media_player.setMedia(media_content, buffer)
            self.media_player.play()

            print(f"🎵 Воспроизводится: {chord_name}, вариант {variant}")
            return True

        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")
            return False


class StandaloneChordConfigTab(QWidget):
    """Вкладка конфигурации аккордов для автономных данных"""

    def __init__(self):
        super().__init__()

        # Загружаем автономные данные
        try:
            self.chords_loader = ChordsDataLoader()
            print("✅ Автономные данные загружены")
        except ImportError as e:
            print(f"❌ Ошибка загрузки автономных данных: {e}")
            # Здесь можно добавить fallback на старую систему
            return

        self.current_display_type = "fingers"
        self.current_scale_type = "small1"
        self.current_fret_type = "roman"
        self.current_barre_outline = "none"
        self.current_note_outline = "none"
        self.current_group = None
        self.current_chords = []
        self.current_chord = None
        self.original_pixmap = None

        # Плеер звуков для автономных данных
        self.sound_player = StandaloneChordSoundPlayer(self.chords_loader)

        self.initUI()
        self.load_standalone_configuration()

    def initUI(self):
        """Инициализация интерфейса (аналогично оригинальному)"""
        layout = QVBoxLayout(self)

        # Верхняя панель с настройками
        top_layout = QHBoxLayout()

        # Комбобокс выбора масштаба
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Маленький 1", "Маленький 2", "Средний 1", "Средний 2", "Оригинальный размер"])
        self.scale_combo.currentTextChanged.connect(self.on_scale_changed)
        top_layout.addWidget(QLabel("Масштаб:"))
        top_layout.addWidget(self.scale_combo)

        # Комбобокс выбора типа отображения
        self.display_type_combo = QComboBox()
        self.display_type_combo.addItems(["Пальцы", "Ноты"])
        self.display_type_combo.currentTextChanged.connect(self.on_display_type_changed)
        top_layout.addWidget(QLabel("Тип:"))
        top_layout.addWidget(self.display_type_combo)

        # Комбобокс выбора типа ладов
        self.fret_type_combo = QComboBox()
        self.fret_type_combo.addItems(["Римские", "Обычные"])
        self.fret_type_combo.currentTextChanged.connect(self.on_fret_type_changed)
        top_layout.addWidget(QLabel("Лад:"))
        top_layout.addWidget(self.fret_type_combo)

        # Комбобокс обводки барре
        self.barre_outline_combo = QComboBox()
        self.barre_outline_combo.addItems(["Без обводки", "Тонкая", "Средняя", "Толстая"])
        self.barre_outline_combo.currentTextChanged.connect(self.on_barre_outline_changed)
        top_layout.addWidget(QLabel("Обводка барре:"))
        top_layout.addWidget(self.barre_outline_combo)

        # Комбобокс обводки нот
        self.note_outline_combo = QComboBox()
        self.note_outline_combo.addItems(["Без обводки", "Тонкая", "Средняя", "Толстая"])
        self.note_outline_combo.currentTextChanged.connect(self.on_note_outline_changed)
        top_layout.addWidget(QLabel("Обводка нот:"))
        top_layout.addWidget(self.note_outline_combo)

        # Комбобокс выбора группы аккордов
        self.group_combo = QComboBox()
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        top_layout.addWidget(QLabel("Группа:"))
        top_layout.addWidget(self.group_combo)

        top_layout.setSpacing(5)
        layout.addLayout(top_layout)

        # Ряд для аккордов
        chords_row_layout = QHBoxLayout()
        chords_label = QLabel("Аккорды:")
        chords_label.setFixedWidth(60)
        chords_row_layout.addWidget(chords_label)

        # Scroll area для кнопок аккордов
        self.chords_scroll = QScrollArea()
        self.chords_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chords_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chords_scroll.setFixedHeight(45)
        self.chords_widget = QWidget()
        self.chords_layout = QHBoxLayout(self.chords_widget)
        self.chords_layout.setContentsMargins(5, 5, 5, 5)
        self.chords_layout.setSpacing(3)
        self.chords_scroll.setWidget(self.chords_widget)
        self.chords_scroll.setWidgetResizable(True)

        chords_row_layout.addWidget(self.chords_scroll, 1)
        layout.addLayout(chords_row_layout)

        # Секция информации об аккорде
        self.create_chord_info_section(layout)

        # Область для изображения
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.image_label.setText("Загрузка автономных данных...")
        self.image_label.setMinimumSize(400, 300)
        self.image_scroll.setWidget(self.image_label)
        layout.addWidget(self.image_scroll, 1)

    def create_chord_info_section(self, layout):
        """Создание секции информации об аккорде"""
        info_container = QWidget()
        info_layout = QHBoxLayout(info_container)
        info_layout.setContentsMargins(8, 8, 8, 8)

        # Метка с информацией
        self.chord_info_label = QLabel("Выберите аккорд для отображения информации")
        self.chord_info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.chord_info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Кнопка воспроизведения звука
        self.play_sound_btn = QPushButton("🎵 Послушать")
        self.play_sound_btn.setFixedSize(120, 40)
        self.play_sound_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.play_sound_btn.clicked.connect(self.play_current_chord_sound)
        self.play_sound_btn.setEnabled(False)

        info_layout.addWidget(self.chord_info_label, 1)
        info_layout.addWidget(self.play_sound_btn)
        info_container.setFixedHeight(60)
        layout.addWidget(info_container)

    def load_standalone_configuration(self):
        """Загрузка конфигурации из автономных данных"""
        try:
            # Загружаем шаблон изображения
            template_data = self.chords_loader.get_template_image_data()
            if template_data:
                self.original_pixmap = QPixmap()
                self.original_pixmap.loadFromData(template_data)
                if not self.original_pixmap.isNull():
                    self.display_original_image()
                    print("✅ Шаблон изображения загружен из автономных данных")
                else:
                    self.image_label.setText("Ошибка загрузки шаблона")
            else:
                self.image_label.setText("Шаблон не найден в автономных данных")

            # Загружаем группы аккордов
            groups = self.get_chord_groups()
            self.group_combo.clear()
            self.group_combo.addItems(groups)

            if groups:
                self.current_group = groups[0]
                self.load_chord_buttons()
            else:
                self.image_label.setText("Группы аккордов не найдены")

            # Выводим статистику
            self.chords_loader.print_stats()

        except Exception as e:
            error_msg = f"Ошибка загрузки автономных данных: {str(e)}"
            self.image_label.setText(error_msg)
            print(f"❌ {error_msg}")

    def get_chord_groups(self):
        """Получение списка групп аккордов из автономных данных"""
        groups = set()
        for chord_name in self.chords_loader.get_chord_names():
            chord_data = self.chords_loader.get_chord_data(chord_name)
            if chord_data:
                group = chord_data.get('group', 'unknown')
                groups.add(group)
        return sorted(list(groups))

    def get_chords_by_group(self, group):
        """Получение аккордов по группе из автономных данных"""
        chords = []
        for chord_name in self.chords_loader.get_chord_names():
            chord_data = self.chords_loader.get_chord_data(chord_name)
            if chord_data and chord_data.get('group') == group:
                chords.append({
                    'name': chord_name,
                    'data': chord_data  # Все данные аккорда
                })
        return sorted(chords, key=lambda x: x['name'])

    def load_chord_buttons(self):
        """Загрузка кнопок аккордов для текущей группы"""
        try:
            # Очищаем layout
            for i in reversed(range(self.chords_layout.count())):
                widget = self.chords_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Получаем аккорды для текущей группы
            self.current_chords = self.get_chords_by_group(self.current_group)

            if not self.current_chords:
                label = QLabel("Аккорды не найдены")
                self.chords_layout.addWidget(label)
                return

            # Создаем кнопки
            for chord_info in self.current_chords:
                try:
                    chord_name = chord_info['name']

                    # Создаем кнопку с номером варианта (по умолчанию 1)
                    btn = QPushButton("1")
                    btn.setFixedSize(40, 30)
                    btn.setStyleSheet("""
                        QPushButton {
                            font-size: 10px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #e0e0e0;
                        }
                    """)

                    # Добавляем подсказку
                    chord_data = chord_info['data']
                    description = chord_data.get('description', chord_name)
                    btn.setToolTip(f"{chord_name} - {description}")

                    btn.clicked.connect(lambda checked, c=chord_info: self.on_chord_clicked(c))
                    self.chords_layout.addWidget(btn)

                except Exception as e:
                    print(f"Ошибка при создании кнопки аккорда: {e}")
                    continue

            # Автоматически загружаем первый аккорд группы
            if self.current_chords:
                self.current_chord = self.current_chords[0]
                self.display_chord(self.current_chord)
                self.update_chord_info(self.current_chord)

        except Exception as e:
            print(f"Ошибка при загрузке кнопок аккордов: {e}")
            label = QLabel("Ошибка загрузки аккордов")
            self.chords_layout.addWidget(label)

    def on_chord_clicked(self, chord_info):
        """Обработчик клика по кнопке аккорда"""
        self.current_chord = chord_info
        self.display_chord(chord_info)
        self.update_chord_info(chord_info)

    def update_chord_info(self, chord_info):
        """Обновление информации о выбранном аккорде"""
        try:
            if chord_info:
                chord_data = chord_info['data']
                chord_name = chord_info['name']
                description = chord_data.get('description', 'Не указано')
                chord_type = chord_data.get('type', 'Не указан')

                info_text = f"<b>Аккорд:</b> {chord_name} | <b>Название:</b> {description} | <b>Тип:</b> {chord_type}"
                self.chord_info_label.setText(info_text)

                # Включаем кнопку воспроизведения если есть звук
                has_sound = any(variant.get('sound_data') for variant in chord_data.get('variants', []))
                self.play_sound_btn.setEnabled(has_sound)

            else:
                self.chord_info_label.setText("Информация об аккорде недоступна")
                self.play_sound_btn.setEnabled(False)

        except Exception as e:
            print(f"Ошибка при обновлении информации об аккорде: {e}")
            self.chord_info_label.setText("Ошибка загрузки информации")
            self.play_sound_btn.setEnabled(False)

    def play_current_chord_sound(self):
        """Воспроизведение звука текущего аккорда"""
        if not self.current_chord:
            return

        try:
            chord_name = self.current_chord['name']

            # Меняем стиль кнопки на время воспроизведения
            self.play_sound_btn.setText("▶️ Играет...")
            self.play_sound_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self.play_sound_btn.setEnabled(False)

            # Воспроизводим звук (вариант 1 по умолчанию)
            success = self.sound_player.play_chord_sound(chord_name, 1)

            if not success:
                print(f"❌ Не удалось воспроизвести звук для аккорда {chord_name}")

            # Восстанавливаем кнопку через 0.5 секунды
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, self.restore_play_button)

        except Exception as e:
            print(f"❌ Ошибка при воспроизведении звука: {e}")
            self.restore_play_button()

    def restore_play_button(self):
        """Восстановление обычного состояния кнопки"""
        self.play_sound_btn.setText("🎵 Послушать")
        self.play_sound_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.play_sound_btn.setEnabled(True)

    def display_original_image(self):
        """Отображение оригинального изображения"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def display_chord(self, chord_info):
        """Отображение выбранного аккорда"""
        try:
            if not self.original_pixmap or self.original_pixmap.isNull():
                self.image_label.setText("Ошибка: изображение не загружено")
                return

            chord_name = chord_info['name']
            chord_data = chord_info['data']

            # Получаем JSON параметры для отрисовки (вариант 1 по умолчанию)
            json_params = None
            variants = chord_data.get('variants', [])
            if variants:
                # Берем первый вариант
                variant_data = variants[0]
                json_params = variant_data.get('json_parameters', {})

            if not json_params:
                self.image_label.setText(f"Нет данных для отрисовки аккорда {chord_name}")
                return

            # Здесь должна быть логика отрисовки аккорда на основе json_params
            # Аналогично оригинальному display_chord, но с использованием json_params
            self.draw_chord_from_json_params(json_params, chord_name)

        except Exception as e:
            self.image_label.setText(f"Ошибка отображения: {str(e)}")
            print(f"Ошибка при отображении аккорда: {e}")

    def draw_chord_from_json_params(self, json_params, chord_name):
        """Отрисовка аккорда на основе JSON параметров"""
        try:
            # Получаем область обрезки
            crop_rect = json_params.get('crop_rect', [])

            # Получаем элементы для отображения в зависимости от типа
            if self.current_display_type == "fingers":
                elements = json_params.get('elements_fingers', [])
            else:
                elements = json_params.get('elements_notes', [])

            # Получаем настройки отображения
            display_settings = json_params.get('display_settings', {})

            print(f"🎨 Отрисовка аккорда {chord_name}: {len(elements)} элементов")

            # Здесь должна быть полная логика отрисовки как в оригинальном display_chord
            # С использованием crop_rect, elements, display_settings

            # Временная заглушка - просто показываем оригинальное изображение
            self.display_original_image()

        except Exception as e:
            print(f"❌ Ошибка отрисовки аккорда: {e}")

    # Остальные методы обработчиков изменений (аналогично оригинальным)
    def on_scale_changed(self, scale_type):
        scale_map = {
            "Маленький 1": "small1",
            "Маленький 2": "small2",
            "Средний 1": "medium1",
            "Средний 2": "medium2"
        }
        self.current_scale_type = scale_map.get(scale_type, "original")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_display_type_changed(self, display_type):
        self.current_display_type = "fingers" if display_type == "Пальцы" else "notes"
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_fret_type_changed(self, fret_type):
        self.current_fret_type = "roman" if fret_type == "Римские" else "numeric"
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_barre_outline_changed(self, outline_type):
        outline_map = {
            "Без обводки": "none",
            "Тонкая": "thin",
            "Средняя": "medium",
            "Толстая": "thick"
        }
        self.current_barre_outline = outline_map.get(outline_type, "none")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_note_outline_changed(self, outline_type):
        outline_map = {
            "Без обводки": "none",
            "Тонкая": "thin",
            "Средняя": "medium",
            "Толстая": "thick"
        }
        self.current_note_outline = outline_map.get(outline_type, "none")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_group_changed(self, group):
        self.current_group = group
        self.load_chord_buttons()


class StandaloneMainWindow(QMainWindow):
    """Главное окно для автономного приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord App - Standalone Version")
        self.setGeometry(100, 100, 1200, 800)

        # Создаем центральный виджет
        self.central_widget = StandaloneChordConfigTab()
        self.setCentralWidget(self.central_widget)

        # Создаем минибар
        self.create_mini_toolbar()

    def create_mini_toolbar(self):
        """Создание минибара с кнопками"""
        toolbar = QToolBar("Минибар")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Кнопка информации
        info_action = QAction("ℹ️ О программе", self)
        info_action.triggered.connect(self.show_about)
        toolbar.addAction(info_action)

        toolbar.addSeparator()

    def show_about(self):
        """Показывает информацию о программе"""
        QMessageBox.information(self, "О программе",
                                "Автономное приложение аккордов\n"
                                "Все данные хранятся в chords_data.py\n"
                                "Версия: 2.0 (Standalone)")


def main():
    """Основная функция запуска автономного приложения"""
    app = QApplication(sys.argv)

    # Проверяем доступность автономных данных
    if not HAS_STANDALONE_DATA:
        QMessageBox.critical(None, "Ошибка",
                             "Файл chords_data.py не найден!\n\n"
                             "Запустите сначала конвертер:\n"
                             "python run_standalone_converter.py")
        return

    window = StandaloneMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()