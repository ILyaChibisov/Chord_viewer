from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QComboBox, QLabel, QScrollArea, QGridLayout,
                             QGroupBox, QMessageBox, QSizePolicy, QFileDialog, QMainWindow, QApplication, QToolBar,
                             QAction)
from PyQt5.QtCore import Qt, QSize, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
import os
import pandas as pd
import json
import openpyxl
import subprocess
import sys
import re

from chord_config_manager import ChordConfigManager


class ChordConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ChordConfigManager()
        self.current_display_type = "fingers"  # fingers или notes
        self.current_scale_type = "small1"  # small1, small2, medium1, medium2 или original
        self.current_fret_type = "roman"  # roman или numeric
        self.current_barre_outline = "none"  # none, thin, medium, thick
        self.current_note_outline = "none"  # none, thin, medium, thick
        self.current_group = None
        self.current_chords = []
        self.current_chord = None
        self.original_pixmap = None  # Сохраняем оригинальное изображение

        self.initUI()
        self.load_configuration()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Верхняя панель с настройками - ТОЛЬКО КОМБОБОКСЫ
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

        # ОТДЕЛЬНЫЙ РЯД ДЛЯ АККОРДОВ - ниже основной панели
        chords_row_layout = QHBoxLayout()

        # Метка "Аккорды:"
        chords_label = QLabel("Аккорды:")
        chords_label.setFixedWidth(60)  # Фиксированная ширина для выравнивания
        chords_row_layout.addWidget(chords_label)

        # Scroll area для кнопок аккордов
        self.chords_scroll = QScrollArea()
        self.chords_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chords_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chords_scroll.setFixedHeight(45)  # Минимальная высота
        self.chords_widget = QWidget()
        self.chords_layout = QHBoxLayout(self.chords_widget)  # Горизонтальный layout
        self.chords_layout.setContentsMargins(5, 5, 5, 5)
        self.chords_layout.setSpacing(3)  # Минимальный отступ между кнопками
        self.chords_scroll.setWidget(self.chords_widget)
        self.chords_scroll.setWidgetResizable(True)

        chords_row_layout.addWidget(self.chords_scroll, 1)  # Растягиваем на оставшееся место

        layout.addLayout(chords_row_layout)

        # ИНФОРМАЦИЯ О ВЫБРАННОМ АККОРДЕ
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
        self.chord_info_label.setAlignment(Qt.AlignCenter)
        self.chord_info_label.setFixedHeight(40)
        layout.addWidget(self.chord_info_label)

        # Область для изображения с прокруткой
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.image_label.setText("Загрузка...")
        self.image_label.setMinimumSize(400, 300)  # Оригинальный минимальный размер
        self.image_scroll.setWidget(self.image_label)
        layout.addWidget(self.image_scroll, 1)  # Растягиваем область с изображением

    def on_scale_changed(self, scale_type):
        """Обработчик изменения масштаба"""
        if scale_type == "Маленький 1":
            self.current_scale_type = "small1"
        elif scale_type == "Маленький 2":
            self.current_scale_type = "small2"
        elif scale_type == "Средний 1":
            self.current_scale_type = "medium1"
        elif scale_type == "Средний 2":
            self.current_scale_type = "medium2"
        else:
            self.current_scale_type = "original"

        if self.current_chord:
            self.display_chord(self.current_chord)
        elif self.original_pixmap:
            self.display_original_image()

    def on_display_type_changed(self, display_type):
        """Обработчик изменения типа отображения"""
        self.current_display_type = "fingers" if display_type == "Пальцы" else "notes"
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_fret_type_changed(self, fret_type):
        """Обработчик изменения типа отображения ладов"""
        self.current_fret_type = "roman" if fret_type == "Римские" else "numeric"
        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_barre_outline_changed(self, outline_type):
        """Обработчик изменения обводки барре"""
        if outline_type == "Без обводки":
            self.current_barre_outline = "none"
        elif outline_type == "Тонкая":
            self.current_barre_outline = "thin"
        elif outline_type == "Средняя":
            self.current_barre_outline = "medium"
        else:  # "Толстая"
            self.current_barre_outline = "thick"

        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_note_outline_changed(self, outline_type):
        """Обработчик изменения обводки нот"""
        if outline_type == "Без обводки":
            self.current_note_outline = "none"
        elif outline_type == "Тонкая":
            self.current_note_outline = "thin"
        elif outline_type == "Средняя":
            self.current_note_outline = "medium"
        else:  # "Толстая"
            self.current_note_outline = "thick"

        if self.current_chord:
            self.display_chord(self.current_chord)

    def on_group_changed(self, group):
        """Обработчик изменения группы аккордов"""
        self.current_group = group
        self.load_chord_buttons()

        # АВТОМАТИЧЕСКИ ЗАГРУЖАЕМ ПЕРВЫЙ АККОРД НОВОЙ ГРУППЫ
        if self.current_chords:
            self.current_chord = self.current_chords[0]
            self.display_chord(self.current_chord)
            self.update_chord_info(self.current_chord)
        else:
            self.current_chord = None
            self.chord_info_label.setText("Аккорды не найдены")
            if self.original_pixmap:
                self.display_original_image()
            else:
                self.image_label.setText("Аккорды не найдены")

    def on_chord_clicked(self, chord_info):
        """Обработчик клика по кнопке аккорда"""
        self.current_chord = chord_info
        self.display_chord(chord_info)
        self.update_chord_info(chord_info)

    def update_chord_info(self, chord_info):
        """Обновление информации о выбранном аккорде"""
        try:
            if chord_info and 'data' in chord_info:
                data = chord_info['data']
                chord = data.get('CHORD', 'Не указан')
                caption = data.get('CAPTION', 'Не указано')
                chord_type = data.get('TYPE', 'Не указан')
                variant = data.get('VARIANT', '1')

                # Формируем текст информации
                info_text = f"<b>Аккорд:</b> {chord} | <b>Название:</b> {caption} | <b>Тип:</b> {chord_type} | <b>Вариант:</b> {variant}"
                self.chord_info_label.setText(info_text)
            else:
                self.chord_info_label.setText("Информация об аккорде недоступна")
        except Exception as e:
            print(f"Ошибка при обновлении информации об аккорде: {e}")
            self.chord_info_label.setText("Ошибка загрузки информации")

    def get_variant_number(self, chord_name, variant):
        """Получение номера варианта для отображения на кнопке"""
        try:
            # Сначала пробуем получить из поля VARIANT
            if variant and str(variant).isdigit():
                return str(variant)

            # Если вариант не указан, пытаемся извлечь из имени аккорда
            # Например: "A1" -> "1", "Am2" -> "2"
            if chord_name:
                match = re.search(r'(\d+)$', str(chord_name))
                if match:
                    return match.group(1)

            # Если ничего не нашли, возвращаем "1" по умолчанию
            return "1"
        except Exception as e:
            print(f"Ошибка в get_variant_number: {e}")
            return "1"

    def load_chord_buttons(self):
        """Загрузка кнопок аккордов для текущей группы"""
        try:
            # Очищаем layout
            for i in reversed(range(self.chords_layout.count())):
                widget = self.chords_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Получаем аккорды для текущей группы
            self.current_chords = self.config_manager.get_chords_by_group(self.current_group)

            if not self.current_chords:
                label = QLabel("Аккорды не найдены")
                self.chords_layout.addWidget(label)
                return

            # Создаем кнопки - все в одну строку
            for chord_info in self.current_chords:
                try:
                    chord_data = chord_info.get('data', {})
                    chord_name = chord_info.get('name', '')
                    variant = chord_data.get('VARIANT', '')

                    # Определяем текст для кнопки - только номер варианта
                    button_text = self.get_variant_number(chord_name, variant)

                    btn = QPushButton(button_text)
                    btn.setFixedSize(40, 30)  # Еще меньше, так как только цифры
                    btn.setStyleSheet("""
                        QPushButton {
                            font-size: 10px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #e0e0e0;
                        }
                    """)

                    # Добавляем всплывающую подсказку с полным названием
                    full_name = f"{chord_data.get('CHORD', '')}{variant}"
                    caption = chord_data.get('CAPTION', '')
                    tooltip = f"{full_name} - {caption}" if caption else full_name
                    btn.setToolTip(tooltip)

                    btn.clicked.connect(lambda checked, c=chord_info: self.on_chord_clicked(c))
                    self.chords_layout.addWidget(btn)
                except Exception as e:
                    print(f"Ошибка при создании кнопки аккорда: {e}")
                    continue

            # АВТОМАТИЧЕСКИ ЗАГРУЖАЕМ ПЕРВЫЙ АККОРД ГРУППЫ
            if self.current_chords:
                self.current_chord = self.current_chords[0]
                self.display_chord(self.current_chord)
                self.update_chord_info(self.current_chord)

        except Exception as e:
            print(f"Ошибка при загрузке кнопок аккордов: {e}")
            label = QLabel("Ошибка загрузки аккордов")
            self.chords_layout.addWidget(label)

    def load_configuration(self):
        """Загрузка конфигурации"""
        try:
            if self.config_manager.load_config_data():
                # Загружаем оригинальное изображение
                if os.path.exists(self.config_manager.image_path):
                    self.original_pixmap = QPixmap(self.config_manager.image_path)
                    if not self.original_pixmap.isNull():
                        # Показываем оригинальное изображение при запуске
                        self.display_original_image()
                    else:
                        self.image_label.setText("Ошибка загрузки изображения")
                else:
                    self.image_label.setText(f"Изображение не найдено: {self.config_manager.image_path}")

                # Заполняем комбобокс групп
                groups = self.config_manager.get_chord_groups()
                self.group_combo.clear()
                self.group_combo.addItems(groups)

                if groups:
                    self.current_group = groups[0]
                    self.load_chord_buttons()
                else:
                    self.image_label.setText("Группы аккордов не найдены")
            else:
                self.image_label.setText("Ошибка загрузки конфигурации. Проверьте файлы в папке templates2")
        except Exception as e:
            error_msg = f"Ошибка при загрузке конфигурации: {str(e)}"
            self.image_label.setText(error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def display_original_image(self):
        """Отображение оригинального изображения при запуске с масштабированием"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Масштабируем изображение для отображения (оригинальный размер)
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            print(
                f"📏 Оригинальное изображение: {self.original_pixmap.width()}x{self.original_pixmap.height()} -> {scaled_pixmap.width()}x{scaled_pixmap.height()}")

    def refresh_configuration(self):
        """Обновление конфигурации из Excel файла"""
        try:
            print("🔄 Обновление конфигурации...")

            # Сохраняем текущее состояние
            current_group = self.current_group
            current_chord = self.current_chord

            # Перезагружаем данные
            if self.config_manager.load_config_data():
                # Перезагружаем изображение
                if os.path.exists(self.config_manager.image_path):
                    self.original_pixmap = QPixmap(self.config_manager.image_path)

                # Обновляем комбобокс групп
                groups = self.config_manager.get_chord_groups()
                self.group_combo.clear()
                self.group_combo.addItems(groups)

                if groups:
                    # Пытаемся восстановить предыдущее состояние
                    if current_group in groups:
                        self.current_group = current_group
                        self.group_combo.setCurrentText(current_group)
                    else:
                        self.current_group = groups[0]
                        self.group_combo.setCurrentText(groups[0])

                    self.load_chord_buttons()

                    # Пытаемся восстановить предыдущий аккорд
                    if current_chord:
                        chord_names = [chord['name'] for chord in self.current_chords]
                        if current_chord['name'] in chord_names:
                            # Находим и активируем кнопку нужного аккорда
                            index = chord_names.index(current_chord['name'])
                            self.current_chord = self.current_chords[index]
                            self.display_chord(self.current_chord)
                            self.update_chord_info(self.current_chord)
                        else:
                            # Показываем первый аккорд группы
                            self.current_chord = self.current_chords[0]
                            self.display_chord(self.current_chord)
                            self.update_chord_info(self.current_chord)
                    else:
                        # Показываем первый аккорд группы
                        self.current_chord = self.current_chords[0]
                        self.display_chord(self.current_chord)
                        self.update_chord_info(self.current_chord)
                else:
                    self.image_label.setText("Группы аккордов не найдены после обновления")

                print("✅ Конфигурация обновлена успешно")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить конфигурацию из Excel файла")
                print("❌ Ошибка обновления конфигурации")

        except Exception as e:
            error_msg = f"Ошибка при обновлении конфигурации: {str(e)}"
            QMessageBox.critical(self, "Ошибка", error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def refresh_colors(self):
        """Обновление цветов из Excel файла"""
        try:
            print("🎨 Обновление цветов...")

            # Запускаем функцию обновления цветов напрямую
            success = self.update_note_styles_no_pandas()

            if success:
                # Перезагружаем конфигурацию для применения новых цветов
                self.refresh_configuration()
                QMessageBox.information(self, "Успех", "Цвета успешно обновлены!")
                print("✅ Цвета обновлены успешно")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить цвета")
                print("❌ Ошибка обновления цветов")

        except Exception as e:
            error_msg = f"Ошибка при обновлении цветов: {str(e)}"
            QMessageBox.critical(self, "Ошибка", error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def update_note_styles_no_pandas(self):
        """
        Версия без использования pandas - встроенная в класс
        """
        excel_path = os.path.join("source", "chord_config.xlsx")
        json_path = os.path.join("source", "template.json")

        try:
            print("Чтение Excel файла...")
            workbook = openpyxl.load_workbook(excel_path)
            sheet = workbook['COLOR']

            # Создаем словари для сопоставления нот и стилей, а также для барре
            note_to_style = {}
            barre_style = None

            # Находим колонки
            headers = [cell.value for cell in sheet[1]]
            try:
                ton_col = headers.index('ton')
                color_col = headers.index('color')
            except ValueError:
                print("Ошибка: В таблице должны быть колонки 'ton' и 'color'")
                return False

            # Читаем данные
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                if row[ton_col] and row[color_col]:
                    note_name = str(row[ton_col]).strip()
                    style_name = str(row[color_col]).strip()

                    if note_name.lower() == 'barre':
                        barre_style = style_name
                        print(f"Загружен стиль для барре: {barre_style}")
                    else:
                        note_to_style[note_name] = style_name
                        print(f"Загружено: {note_name} -> {style_name}")

            print(f"Всего загружено {len(note_to_style)} соответствий для нот")
            if barre_style:
                print(f"Стиль для барре: {barre_style}")

            # Чтение и обновление JSON
            print("Чтение JSON файла...")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            updated_notes_count = 0
            updated_barre_count = 0

            # Обновляем ноты (раздел 'notes')
            if 'notes' in data:
                for note_key, note_data in data['notes'].items():
                    if 'note_name' in note_data:
                        note_name = note_data['note_name']
                        if note_name in note_to_style:
                            old_style = note_data.get('style', 'не установлен')
                            note_data['style'] = note_to_style[note_name]
                            updated_notes_count += 1
                            print(
                                f"Обновлена нота: {note_key} - '{note_name}' - '{old_style}' -> '{note_to_style[note_name]}'")
            else:
                print("Раздел 'notes' не найден в JSON")

            # Обновляем барре (раздел 'barres')
            if 'barres' in data and barre_style:
                for barre_key, barre_data in data['barres'].items():
                    old_style = barre_data.get('style', 'не установлен')
                    barre_data['style'] = barre_style
                    updated_barre_count += 1
                    print(f"Обновлено барре: {barre_key} - '{old_style}' -> '{barre_style}'")
            else:
                if 'barres' not in data:
                    print("Раздел 'barres' не найден в JSON")
                if not barre_style:
                    print("Стиль для барре не задан в Excel")

            # Сохранение
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Готово! Обновлено {updated_notes_count} нот и {updated_barre_count} барре")
            return True

        except Exception as e:
            print(f"Ошибка: {e}")
            return False

    def save_chord_configuration(self):
        """Сохранение конфигурации всех аккордов в JSON файл"""
        try:
            if not self.config_manager.chord_data:
                QMessageBox.warning(self, "Ошибка", "Нет данных аккордов для сохранения")
                return

            # Запрашиваем путь для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить конфигурацию аккордов",
                "chords_configuration.json",
                "JSON Files (*.json)"
            )

            if not file_path:
                return

            print("💾 Сохранение конфигурации аккордов...")

            # Создаем структуру для сохранения
            config_data = {
                "metadata": {
                    "image_file": os.path.basename(self.config_manager.image_path),
                    "total_chords": len(self.config_manager.chord_data),
                    "outline_settings": {
                        "barre_outline": self.current_barre_outline,
                        "note_outline": self.current_note_outline,
                        "scale_type": "original"  # Всегда оригинальный масштаб
                    },
                    "created_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "chords": {}
            }

            # Получаем данные из таблицы CHORDS для каждого аккорда
            chords_info = {}
            for chord in self.config_manager.chord_data:
                chord_name = chord.get('CHORD', '')
                variant = chord.get('VARIANT', '')
                caption = chord.get('CAPTION', '')
                chord_type = chord.get('TYPE', '')

                if chord_name:
                    full_name = f"{chord_name}{variant}" if variant else chord_name
                    chords_info[full_name] = {
                        "base_chord": chord_name,
                        "variant": variant,
                        "caption": caption,
                        "type": chord_type,
                        "ram": chord.get('RAM'),
                        "bar": chord.get('BAR'),
                        "fnl": chord.get('FNL'),
                        "fn": chord.get('FN'),
                        "fpol": chord.get('FPOL'),
                        "fpxl": chord.get('FPXL'),
                        "fp1": chord.get('FP1'),
                        "fp2": chord.get('FP2'),
                        "fp3": chord.get('FP3'),
                        "fp4": chord.get('FP4')
                    }

            # Добавляем информацию о группах
            config_data["groups"] = self.config_manager.get_chord_groups()

            # Собираем полную конфигурацию для каждого аккорда
            total_saved = 0
            for group in config_data["groups"]:
                chords_in_group = self.config_manager.get_chords_by_group(group)
                for chord_info in chords_in_group:
                    chord_name = chord_info['name']

                    # Получаем элементы для обоих типов отображения
                    elements_fingers = self.config_manager.get_chord_elements(
                        chord_info['data'], "fingers"
                    )
                    elements_notes = self.config_manager.get_chord_elements(
                        chord_info['data'], "notes"
                    )

                    # Получаем область обрезки
                    ram_key = chord_info['data'].get('RAM')
                    crop_rect = self.config_manager.get_ram_crop_area(ram_key)

                    # Сохраняем конфигурацию аккорда
                    config_data["chords"][chord_name] = {
                        "group": group,
                        "base_info": chords_info.get(chord_name, {}),
                        "crop_rect": crop_rect,
                        "elements_fingers": self._serialize_elements(elements_fingers),
                        "elements_notes": self._serialize_elements(elements_notes),
                        "display_settings": {
                            "fret_type": self.current_fret_type,
                            "barre_outline": self.current_barre_outline,
                            "note_outline": self.current_note_outline
                        }
                    }
                    total_saved += 1

            # Сохраняем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Успех",
                f"Конфигурация сохранена!\n"
                f"Аккордов: {total_saved}\n"
                f"Файл: {os.path.basename(file_path)}"
            )
            print(f"✅ Конфигурация сохранена: {total_saved} аккордов")

        except Exception as e:
            error_msg = f"Ошибка при сохранении конфигурации: {str(e)}"
            QMessageBox.critical(self, "Ошибка", error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def _serialize_elements(self, elements):
        """Сериализация элементов для сохранения в JSON"""
        serialized = []
        for element in elements:
            element_data = {
                "type": element['type'],
                "data": element['data'].copy()
            }
            # Убираем временные поля
            if '_key' in element_data['data']:
                del element_data['data']['_key']
            serialized.append(element_data)
        return serialized

    def apply_outline_settings(self, elements):
        """Применение настроек обводки к элементам с улучшенной отрисовкой"""
        # Определяем толщину обводки для барре
        barre_outline_widths = {
            "none": 0,
            "thin": 3,  # Увеличил для лучшей видимости
            "medium": 5,
            "thick": 8
        }

        # Определяем толщину обводки для нот
        note_outline_widths = {
            "none": 0,
            "thin": 2,
            "medium": 3,
            "thick": 5
        }

        barre_width = barre_outline_widths.get(self.current_barre_outline, 0)
        note_width = note_outline_widths.get(self.current_note_outline, 0)

        modified_elements = []
        for element in elements:
            if element['type'] == 'barre' and barre_width > 0:
                # Добавляем улучшенную обводку к барре
                modified_element = element.copy()
                modified_element['data'] = element['data'].copy()
                modified_element['data']['outline_width'] = barre_width
                modified_element['data']['outline_color'] = [0, 0, 0]  # Черный цвет
                modified_elements.append(modified_element)
            elif element['type'] == 'note' and note_width > 0:
                # Добавляем улучшенную обводку к нотам
                modified_element = element.copy()
                modified_element['data'] = element['data'].copy()
                modified_element['data']['outline_width'] = note_width
                modified_element['data']['outline_color'] = [0, 0, 0]  # Черный цвет
                modified_elements.append(modified_element)
            else:
                # Для других элементов оставляем как есть
                modified_elements.append(element)

        return modified_elements

    def draw_elements_with_outline(self, painter, elements, crop_offset=None):
        """Улучшенная отрисовка элементов с обводкой"""
        try:
            # Сначала рисуем все элементы через стандартный метод config_manager
            # но с учетом смещения области обрезки
            if crop_offset:
                crop_x, crop_y, crop_width, crop_height = crop_offset
                self.config_manager.draw_elements_on_canvas(painter, elements,
                                                            (crop_x, crop_y, crop_width, crop_height))
            else:
                self.config_manager.draw_elements_on_canvas(painter, elements, None)

            # Затем рисуем обводку для элементов, у которых она включена
            # Сначала рисуем обводку барре (нижний слой)
            for element in elements:
                element_type = element['type']
                data = element['data']

                if element_type == 'barre' and data.get('outline_width', 0) > 0:
                    self._draw_barre_with_outline(painter, data, crop_offset)

            # Затем рисуем обводку нот (верхний слой - приоритет выше)
            for element in elements:
                element_type = element['type']
                data = element['data']

                if element_type == 'note' and data.get('outline_width', 0) > 0:
                    self._draw_note_with_outline(painter, data, crop_offset)

        except Exception as e:
            print(f"Ошибка при отрисовке элементов с обводкой: {e}")

    def _draw_note_with_outline(self, painter, data, crop_offset=None):
        """Улучшенная отрисовка ноты с обводкой"""
        try:
            x = data.get('x', 0)
            y = data.get('y', 0)
            radius = data.get('radius', 10)
            outline_width = data.get('outline_width', 2)

            # Корректируем координаты с учетом смещения области обрезки
            if crop_offset:
                crop_x, crop_y, _, _ = crop_offset
                x = x - crop_x
                y = y - crop_y

            # Сохраняем настройки painter
            painter.save()

            # Включаем сглаживание для плавных краев
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Рисуем обводку (внешний круг)
            outline_pen = QPen(QColor(0, 0, 0))  # Черный цвет обводки
            outline_pen.setWidth(outline_width)
            outline_pen.setCapStyle(Qt.RoundCap)
            outline_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(x - radius), int(y - radius),
                                int(radius * 2), int(radius * 2))

            # Восстанавливаем настройки painter
            painter.restore()

        except Exception as e:
            print(f"Ошибка при отрисовке ноты с обводкой: {e}")

    def _draw_barre_with_outline(self, painter, data, crop_offset=None):
        """Улучшенная отрисовка барре с обводкой"""
        try:
            x = data.get('x', 0)
            y = data.get('y', 0)
            width = data.get('width', 50)
            height = data.get('height', 20)
            outline_width = data.get('outline_width', 3)
            radius = data.get('radius', 10)  # Радиус скругления углов

            # Корректируем координаты с учетом смещения области обрезки
            if crop_offset:
                crop_x, crop_y, _, _ = crop_offset
                x = x - crop_x
                y = y - crop_y

            # Сохраняем настройки painter
            painter.save()

            # Включаем сглаживание для плавных краев
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Рисуем обводку (внешний прямоугольник)
            outline_pen = QPen(QColor(0, 0, 0))  # Черный цвет обводки
            outline_pen.setWidth(outline_width)
            outline_pen.setCapStyle(Qt.RoundCap)
            outline_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)

            # Рисуем скругленный прямоугольник для обводки
            outline_rect = QRectF(x - width / 2, y - height / 2, width, height)
            painter.drawRoundedRect(outline_rect, radius, radius)

            # Восстанавливаем настройки painter
            painter.restore()

        except Exception as e:
            print(f"Ошибка при отрисовке барре с обводкой: {e}")

    def convert_frets_to_numeric(self, elements):
        """Преобразование римских цифр ладов в обычные цифры"""
        roman_to_numeric = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16'
        }

        converted_elements = []
        for element in elements:
            if element['type'] == 'fret':
                # Создаем копию данных элемента
                converted_element = element.copy()
                fret_data = converted_element['data'].copy()

                # Преобразуем символ лада
                original_symbol = fret_data.get('symbol', 'I')
                if original_symbol in roman_to_numeric:
                    fret_data['symbol'] = roman_to_numeric[original_symbol]
                    print(f"🎯 Преобразован лад: {original_symbol} -> {fret_data['symbol']}")

                converted_element['data'] = fret_data
                converted_elements.append(converted_element)
            else:
                # Для других типов элементов оставляем как есть
                converted_elements.append(element)

        return converted_elements

    def display_chord(self, chord_info):
        """Отображение выбранного аккорда на изображении с выбранным масштабом"""
        try:
            if not self.original_pixmap or self.original_pixmap.isNull():
                self.image_label.setText("Ошибка: изображение не загружено")
                return

            # Получаем область обрезки из RAM для этого конкретного аккорда
            ram_key = chord_info['data'].get('RAM')
            crop_rect = self.config_manager.get_ram_crop_area(ram_key)

            print(f"🎯 Оригинальное изображение: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
            print(f"🎯 Область обрезки для RAM '{ram_key}': {crop_rect}")

            # Получаем элементы для отображения
            elements = self.config_manager.get_chord_elements(
                chord_info['data'],
                self.current_display_type
            )

            print(f"🎯 Отображение аккорда: {chord_info['name']}")
            print(f"📊 Найдено элементов: {len(elements)}")

            # Преобразуем символы ладов в зависимости от выбранного типа
            if self.current_fret_type == "numeric":
                elements = self.convert_frets_to_numeric(elements)

            # Применяем настройки обводки к элементам
            elements = self.apply_outline_settings(elements)

            # ВСЕГДА используем обрезку по RAM, если она определена
            if crop_rect:
                crop_x, crop_y, crop_width, crop_height = crop_rect

                # Проверяем границы и корректируем при необходимости
                crop_x = max(0, min(crop_x, self.original_pixmap.width() - 1))
                crop_y = max(0, min(crop_y, self.original_pixmap.height() - 1))
                crop_width = max(1, min(crop_width, self.original_pixmap.width() - crop_x))
                crop_height = max(1, min(crop_height, self.original_pixmap.height() - crop_y))

                print(f"🎯 Финальная область обрезки: ({crop_x}, {crop_y}, {crop_width}, {crop_height})")

                # СОЗДАЕМ НОВОЕ ИЗОБРАЖЕНИЕ РАЗМЕРОМ С ОБЛАСТЬ ОБРЕЗКИ
                result_pixmap = QPixmap(crop_width, crop_height)
                result_pixmap.fill(Qt.white)  # Белый фон

                # Создаем painter для нового изображения
                painter = QPainter(result_pixmap)

                # Включаем сглаживание для всего изображения
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.TextAntialiasing)

                # Копируем область из оригинального изображения
                painter.drawPixmap(0, 0, self.original_pixmap,
                                   crop_x, crop_y, crop_width, crop_height)

                # Рисуем элементы на НОВОМ изображении с правильными координатами
                # Используем улучшенную отрисовку с обводкой и передаем смещение
                self.draw_elements_with_outline(painter, elements, (crop_x, crop_y, crop_width, crop_height))

                painter.end()

                # Применяем выбранный масштаб
                if self.current_scale_type == "small1":
                    # МАЛЕНЬКИЙ 1 - как было раньше (авто масштаб)
                    display_width = min(400, crop_width)
                    scale_factor = display_width / crop_width
                    display_height = int(crop_height * scale_factor)

                    scaled_pixmap = result_pixmap.scaled(
                        display_width,
                        display_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"📏 Маленький 1: {crop_width}x{crop_height} -> {display_width}x{display_height}")

                elif self.current_scale_type == "small2":
                    # МАЛЕНЬКИЙ 2 - 30% от оригинального
                    display_width = int(crop_width * 0.3)
                    display_height = int(crop_height * 0.3)

                    scaled_pixmap = result_pixmap.scaled(
                        display_width,
                        display_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"📏 Маленький 2 (30%): {crop_width}x{crop_height} -> {display_width}x{display_height}")

                elif self.current_scale_type == "medium1":
                    # СРЕДНИЙ 1 - 50% от оригинального
                    display_width = int(crop_width * 0.5)
                    display_height = int(crop_height * 0.5)

                    scaled_pixmap = result_pixmap.scaled(
                        display_width,
                        display_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"📏 Средний 1 (50%): {crop_width}x{crop_height} -> {display_width}x{display_height}")

                elif self.current_scale_type == "medium2":
                    # СРЕДНИЙ 2 - 70% от оригинального
                    display_width = int(crop_width * 0.7)
                    display_height = int(crop_height * 0.7)

                    scaled_pixmap = result_pixmap.scaled(
                        display_width,
                        display_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"📏 Средний 2 (70%): {crop_width}x{crop_height} -> {display_width}x{display_height}")

                else:
                    # ОРИГИНАЛЬНЫЙ РАЗМЕР
                    self.image_label.setPixmap(result_pixmap)
                    print(f"📏 Оригинальный размер: {crop_width}x{crop_height}")

            else:
                # Если нет обрезки, рисуем на полном изображении
                result_pixmap = QPixmap(self.original_pixmap.size())
                result_pixmap.fill(Qt.white)

                painter = QPainter(result_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)

                painter.drawPixmap(0, 0, self.original_pixmap)
                self.draw_elements_with_outline(painter, elements, None)
                painter.end()

                # Применяем выбранный масштаб
                if self.current_scale_type == "small1":
                    scaled_pixmap = result_pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                elif self.current_scale_type == "small2":
                    display_width = int(result_pixmap.width() * 0.3)
                    display_height = int(result_pixmap.height() * 0.3)
                    scaled_pixmap = result_pixmap.scaled(
                        display_width, display_height,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                elif self.current_scale_type == "medium1":
                    display_width = int(result_pixmap.width() * 0.5)
                    display_height = int(result_pixmap.height() * 0.5)
                    scaled_pixmap = result_pixmap.scaled(
                        display_width, display_height,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                elif self.current_scale_type == "medium2":
                    display_width = int(result_pixmap.width() * 0.7)
                    display_height = int(result_pixmap.height() * 0.7)
                    scaled_pixmap = result_pixmap.scaled(
                        display_width, display_height,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setPixmap(result_pixmap)

        except Exception as e:
            self.image_label.setText(f"Ошибка отображения: {str(e)}")
            print(f"Ошибка при отображении аккорда: {e}")
            import traceback
            traceback.print_exc()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord Configuration Tool")
        self.setGeometry(100, 100, 1200, 800)  # x, y, width, height

        # Создаем центральный виджет и устанавливаем его
        self.central_widget = ChordConfigTab()
        self.setCentralWidget(self.central_widget)

        # СОЗДАЕМ МИНИБАР С КНОПКАМИ
        self.create_mini_toolbar()

    def create_mini_toolbar(self):
        """Создание минибара с кнопками"""
        # Создаем тулбар
        toolbar = QToolBar("Минибар")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Кнопка обновления конфигурации (Шаблоны)
        refresh_action = QAction("Шаблоны", self)
        refresh_action.triggered.connect(self.central_widget.refresh_configuration)
        toolbar.addAction(refresh_action)

        # Кнопка обновления цветов
        colors_action = QAction("Цвета", self)
        colors_action.triggered.connect(self.central_widget.refresh_colors)
        toolbar.addAction(colors_action)

        # Кнопка сохранения конфигурации
        save_action = QAction("Сохранить", self)
        save_action.triggered.connect(self.central_widget.save_chord_configuration)
        toolbar.addAction(save_action)

        # Добавляем разделитель для визуального отделения
        toolbar.addSeparator()


def main():
    # Создаем экземпляр приложения
    app = QApplication(sys.argv)

    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()

    # Запускаем цикл событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()