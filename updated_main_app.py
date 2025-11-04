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
from io import BytesIO

# Импортируем наш загрузчик автономных данных
try:
    from chords_data_loader import ChordsDataLoader
    HAS_STANDALONE_DATA = True
except ImportError:
    HAS_STANDALONE_DATA = False
    print("⚠️ chords_data_loader не найден")

from drawing_elements import DrawingElements
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QBuffer, QByteArray

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

            # Создаем медиаконтент из буфера
            media_content = QMediaContent(QUrl.fromLocalFile(""))  # Создаем пустой URL
            self.media_player.setMedia(media_content, buffer)

            # Останавливаем предыдущее воспроизведение и запускаем новое
            self.media_player.stop()
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
                # Создаем QPixmap из bytes
                self.original_pixmap = QPixmap()
                self.original_pixmap.loadFromData(template_data)

                if not self.original_pixmap.isNull():
                    print(f"✅ Шаблон изображения загружен: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
                    self.display_original_image()
                else:
                    self.image_label.setText("Ошибка загрузки шаблона")
                    print("❌ Не удалось загрузить шаблон изображения")
            else:
                self.image_label.setText("Шаблон не найден в автономных данных")
                print("❌ Шаблон изображения не найден в данных")

            # Загружаем группы аккордов
            groups = self.get_chord_groups()
            self.group_combo.clear()
            self.group_combo.addItems(groups)

            if groups:
                self.current_group = groups[0]
                self.load_chord_buttons()
            else:
                self.image_label.setText("Группы аккордов не найдены")
                print("❌ Группы аккордов не найдены")

            # Выводим статистику
            self.chords_loader.print_stats()

        except Exception as e:
            error_msg = f"Ошибка загрузки автономных данных: {str(e)}"
            self.image_label.setText(error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

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
            print(f"🔧 Загружено {len(self.current_chords)} аккордов для группы '{self.current_group}'")

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
                print(f"🎵 Автовыбор первого аккорда: {self.current_chord['name']}")
                self.display_chord(self.current_chord)
                self.update_chord_info(self.current_chord)

        except Exception as e:
            print(f"Ошибка при загрузке кнопок аккордов: {e}")
            label = QLabel("Ошибка загрузки аккордов")
            self.chords_layout.addWidget(label)

    def on_chord_clicked(self, chord_info):
        """Обработчик клика по кнопке аккорда"""
        print(f"🎯 Выбран аккорд: {chord_info['name']}")
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

                print(f"📋 Информация обновлена: {chord_name}, звук: {'✅' if has_sound else '❌'}")

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
            print(f"🔊 Попытка воспроизведения: {chord_name}")
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
            print(f"🖼️ Оригинальное изображение отображено: {scaled_pixmap.width()}x{scaled_pixmap.height()}")

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
                print(f"🎨 Получены JSON параметры для {chord_name}: {len(variants)} вариантов")
            else:
                print(f"❌ Нет вариантов для аккорда {chord_name}")

            if not json_params:
                self.image_label.setText(f"Нет данных для отрисовки аккорда {chord_name}")
                return

            # Отрисовываем аккорд на основе JSON параметров
            self.draw_chord_from_json_params(json_params, chord_name)

        except Exception as e:
            self.image_label.setText(f"Ошибка отображения: {str(e)}")
            print(f"❌ Ошибка при отображении аккорда: {e}")
            import traceback
            traceback.print_exc()

    def draw_chord_from_json_params(self, json_params, chord_name):
        """Отрисовка аккорда на основе JSON параметров"""
        try:
            # Получаем область обрезки
            crop_rect = json_params.get('crop_rect', [])
            print(f"✂️  Область обрезки: {crop_rect}")

            # Получаем элементы для отображения в зависимости от типа
            if self.current_display_type == "fingers":
                elements = json_params.get('elements_fingers', [])
                print(f"👆 Элементы пальцев: {len(elements)}")
            else:
                elements = json_params.get('elements_notes', [])
                print(f"🎵 Элементы нот: {len(elements)}")

            # Получаем настройки отображения
            display_settings = json_params.get('display_settings', {})
            print(f"⚙️  Настройки отображения: {display_settings}")

            # Если есть область обрезки - обрезаем изображение
            if crop_rect and len(crop_rect) == 4:
                crop_x, crop_y, crop_width, crop_height = crop_rect

                # Проверяем границы обрезки
                if (crop_x >= 0 and crop_y >= 0 and
                    crop_x + crop_width <= self.original_pixmap.width() and
                    crop_y + crop_height <= self.original_pixmap.height()):

                    # Создаем обрезанное изображение
                    cropped_pixmap = self.original_pixmap.copy(crop_x, crop_y, crop_width, crop_height)
                    print(f"✂️  Изображение обрезано: {crop_width}x{crop_height}")

                    # Рисуем элементы на обрезанном изображении
                    result_pixmap = self.draw_elements_on_pixmap(cropped_pixmap, elements, display_settings)

                else:
                    print(f"❌ Некорректная область обрезки: {crop_rect}")
                    result_pixmap = self.original_pixmap.copy()
            else:
                print("⚠️ Область обрезки не указана, используем полное изображение")
                result_pixmap = self.original_pixmap.copy()

            # Применяем масштабирование
            final_pixmap = self.apply_scale(result_pixmap)
            self.image_label.setPixmap(final_pixmap)
            print(f"✅ Аккорд {chord_name} отображен: {final_pixmap.width()}x{final_pixmap.height()}")

        except Exception as e:
            print(f"❌ Ошибка отрисовки аккорда: {e}")
            import traceback
            traceback.print_exc()
            # Показываем оригинальное изображение в случае ошибки
            self.display_original_image()

    def draw_elements_on_pixmap(self, pixmap, elements, display_settings):
        """Рисует элементы аккорда на pixmap"""
        try:
            # Создаем копию pixmap для рисования
            result_pixmap = QPixmap(pixmap)
            painter = QPainter(result_pixmap)

            # Включаем сглаживание
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.TextAntialiasing)

            print(f"🎨 Отрисовка {len(elements)} элементов...")

            # Рисуем элементы
            for element in elements:
                element_type = element.get('type')
                element_data = element.get('data', {})

                if element_type == 'fret':
                    DrawingElements.draw_fret(painter, element_data)
                    print(f"   🎯 Лад: {element_data.get('symbol', '?')}")
                elif element_type == 'note':
                    DrawingElements.draw_note(painter, element_data)
                    print(f"   🎵 Нота: {element_data.get('finger', element_data.get('note_name', '?'))}")
                elif element_type == 'barre':
                    DrawingElements.draw_barre(painter, element_data)
                    print(f"   🎸 Баре: {element_data.get('width', 0)}x{element_data.get('height', 0)}")
                else:
                    print(f"   ⚠️ Неизвестный тип элемента: {element_type}")

            painter.end()
            print("✅ Элементы отрисованы")
            return result_pixmap

        except Exception as e:
            print(f"❌ Ошибка отрисовки элементов: {e}")
            return pixmap

    def apply_scale(self, pixmap):
        """Применяет масштабирование к изображению"""
        try:
            if self.current_scale_type == "small1":
                # МАЛЕНЬКИЙ 1 - авто масштаб
                display_width = min(400, pixmap.width())
                scale_factor = display_width / pixmap.width()
                display_height = int(pixmap.height() * scale_factor)

                scaled_pixmap = pixmap.scaled(
                    display_width,
                    display_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                print(f"📏 Маленький 1: {pixmap.width()}x{pixmap.height()} -> {display_width}x{display_height}")

            elif self.current_scale_type == "small2":
                # МАЛЕНЬКИЙ 2 - 30% от оригинального
                display_width = int(pixmap.width() * 0.3)
                display_height = int(pixmap.height() * 0.3)

                scaled_pixmap = pixmap.scaled(
                    display_width,
                    display_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                print(f"📏 Маленький 2 (30%): {pixmap.width()}x{pixmap.height()} -> {display_width}x{display_height}")

            elif self.current_scale_type == "medium1":
                # СРЕДНИЙ 1 - 50% от оригинального
                display_width = int(pixmap.width() * 0.5)
                display_height = int(pixmap.height() * 0.5)

                scaled_pixmap = pixmap.scaled(
                    display_width,
                    display_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                print(f"📏 Средний 1 (50%): {pixmap.width()}x{pixmap.height()} -> {display_width}x{display_height}")

            elif self.current_scale_type == "medium2":
                # СРЕДНИЙ 2 - 70% от оригинального
                display_width = int(pixmap.width() * 0.7)
                display_height = int(pixmap.height() * 0.7)

                scaled_pixmap = pixmap.scaled(
                    display_width,
                    display_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                print(f"📏 Средний 2 (70%): {pixmap.width()}x{pixmap.height()} -> {display_width}x{display_height}")

            else:
                # ОРИГИНАЛЬНЫЙ РАЗМЕР
                scaled_pixmap = pixmap
                print(f"📏 Оригинальный размер: {pixmap.width()}x{pixmap.height()}")

            return scaled_pixmap

        except Exception as e:
            print(f"❌ Ошибка масштабирования: {e}")
            return pixmap

    # Обработчики изменений настроек
    def on_scale_changed(self, scale_type):
        scale_map = {
            "Маленький 1": "small1",
            "Маленький 2": "small2",
            "Средний 1": "medium1",
            "Средний 2": "medium2"
        }
        self.current_scale_type = scale_map.get(scale_type, "original")
        print(f"⚙️  Масштаб изменен: {self.current_scale_type}")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_display_type_changed(self, display_type):
        self.current_display_type = "fingers" if display_type == "Пальцы" else "notes"
        print(f"⚙️  Тип отображения изменен: {self.current_display_type}")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_fret_type_changed(self, fret_type):
        self.current_fret_type = "roman" if fret_type == "Римские" else "numeric"
        print(f"⚙️  Тип ладов изменен: {self.current_fret_type}")
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
        print(f"⚙️  Обводка барре изменена: {self.current_barre_outline}")
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
        print(f"⚙️  Обводка нот изменена: {self.current_note_outline}")
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_group_changed(self, group):
        self.current_group = group
        print(f"⚙️  Группа изменена: {group}")
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