import pandas as pd
import os
import json
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QLinearGradient, QRadialGradient
from PyQt5.QtCore import Qt


class ChordConfigManager:
    def __init__(self):
        self.excel_path = os.path.join("source", "chord_config.xlsx")
        self.template_path = os.path.join("source", "template.json")
        self.image_path = os.path.join("source", "img.png")
        self.chord_data = {}
        self.ram_data = {}
        self.note_data = []  # Данные из листа NOTE
        self.templates = {}

    def load_config_data(self):
        """Загрузка всех данных из Excel и JSON"""
        try:
            # Загружаем Excel файл
            if os.path.exists(self.excel_path):
                # Основной лист с аккордами
                df_chords = pd.read_excel(self.excel_path, sheet_name='CHORDS')
                print("=" * 80)
                print("КОЛОНКИ В EXCEL CHORDS:", df_chords.columns.tolist())

                # Конвертируем в словари
                self.chord_data = df_chords.to_dict('records')
                print(f"Загружено {len(self.chord_data)} аккордов")

                # Загружаем данные RAM
                df_ram = pd.read_excel(self.excel_path, sheet_name='RAM')
                print("КОЛОНКИ В EXCEL RAM:", df_ram.columns.tolist())

                # Сохраняем RAM данные для использования
                self.ram_data = df_ram.to_dict('records')
                print(f"Загружено {len(self.ram_data)} RAM конфигураций")

                # Загружаем данные NOTE
                try:
                    df_note = pd.read_excel(self.excel_path, sheet_name='NOTE')
                    print("КОЛОНКИ В EXCEL NOTE:", df_note.columns.tolist())
                    print("ПЕРВЫЕ 5 СТРОК NOTE:")
                    print(df_note.head())

                    # Сохраняем NOTE данные для использования
                    self.note_data = df_note.to_dict('records')
                    print(f"Загружено {len(self.note_data)} NOTE конфигураций")
                except Exception as e:
                    print(f"⚠️ Лист NOTE не найден или ошибка загрузки: {e}")
                    self.note_data = []

            else:
                print(f"Excel файл не найден: {self.excel_path}")
                return False

            # Загружаем JSON шаблоны
            if os.path.exists(self.template_path):
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                print("JSON шаблоны загружены")

            else:
                print(f"JSON файл не найдена: {self.template_path}")
                return False

            return True

        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_chord_groups(self):
        """Получение списка групп аккордов"""
        groups = set()
        for chord in self.chord_data:
            chord_name = chord.get('CHORD')
            if chord_name:
                chord_name = str(chord_name)
                base_chord = ''.join([c for c in chord_name if c.isalpha()])
                if base_chord:
                    groups.add(base_chord)
        return sorted(list(groups))

    def get_chords_by_group(self, group):
        """Получение аккордов по группе"""
        chords = []
        for chord in self.chord_data:
            chord_name = chord.get('CHORD')
            variant = chord.get('VARIANT')

            if chord_name and variant is not None:
                chord_name = str(chord_name)
                base_chord = ''.join([c for c in chord_name if c.isalpha()])
                if base_chord == group:
                    chords.append({
                        'name': f"{chord_name}{variant}",
                        'chord': chord_name,
                        'variant': variant,
                        'data': chord
                    })
        return sorted(chords, key=lambda x: x['name'])

    def get_ram_crop_area(self, ram_name):
        """Получение области обрезки из RAM в JSON"""
        if not ram_name or self._is_empty_value(ram_name):
            print(f"RAM '{ram_name}' пустой или не найден")
            return None

        ram_name = str(ram_name).strip()
        print(f"🔍 Поиск области обрезки для RAM: '{ram_name}'")

        # Ищем RAM в разделе crop_rects
        if 'crop_rects' in self.templates and ram_name in self.templates['crop_rects']:
            crop_data = self.templates['crop_rects'][ram_name]
            area = (
                crop_data.get('x', 0),
                crop_data.get('y', 0),
                crop_data.get('width', 100),
                crop_data.get('height', 100)
            )
            print(f"✅ Найдена область обрезки '{ram_name}': {area}")
            return area

        print(f"❌ Область обрезки для '{ram_name}' не найдена в JSON")
        return None

    def get_ram_lad_value(self, ram_name):
        """Получение значения LAD для указанного RAM из таблицы RAM"""
        if not ram_name or self._is_empty_value(ram_name):
            return None

        ram_name = str(ram_name).strip()
        print(f"🔍 Поиск LAD для RAM: '{ram_name}'")

        # Ищем RAM в таблице RAM
        for ram_item in self.ram_data:
            item_ram = ram_item.get('RAM')
            if item_ram and str(item_ram).strip() == ram_name:
                lad_value = ram_item.get('LAD')
                print(f"✅ Найден LAD для RAM '{ram_name}': '{lad_value}'")
                return lad_value

        print(f"❌ RAM '{ram_name}' не найден в таблице RAM")
        return None

    def get_ram_elements(self, ram_name):
        """Получение элементов RAM по имени"""
        elements = []
        if not ram_name or self._is_empty_value(ram_name):
            return elements

        ram_name = str(ram_name).strip()

        # Ищем элементы RAM в frets
        if ram_name in self.templates.get('frets', {}):
            element_data = self.templates['frets'][ram_name]
            element_data['_key'] = ram_name
            element_data['type'] = 'fret'  # Явно указываем тип

            elements.append({
                'type': 'fret',
                'data': element_data
            })

        # Ищем элементы с суффиксами (RAM1, RAM2 и т.д.)
        for i in range(1, 5):
            element_key = f"{ram_name}{i}"
            if element_key in self.templates.get('frets', {}):
                element_data = self.templates['frets'][element_key]
                element_data['_key'] = element_key
                element_data['type'] = 'fret'  # Явно указываем тип

                elements.append({
                    'type': 'fret',
                    'data': element_data
                })

        return elements

    def get_ram_elements_from_lad(self, lad_value):
        """Получение элементов RAM на основе значения LAD"""
        elements = []

        if not lad_value or self._is_empty_value(lad_value):
            return elements

        lad_value = str(lad_value).strip()
        print(f"🔍 Поиск элементов для LAD: '{lad_value}'")

        # Разделяем значения по запятой
        lad_keys = [key.strip() for key in lad_value.split(',')]

        for lad_key in lad_keys:
            # Формируем ключ для поиска в JSON (добавляем LAD)
            json_key = f"{lad_key}LAD"
            if json_key in self.templates.get('frets', {}):
                element_data = self.templates['frets'][json_key]
                element_data['_key'] = json_key
                element_data['type'] = 'fret'  # Явно указываем тип

                elements.append({
                    'type': 'fret',
                    'data': element_data
                })
                print(f"✅ Найден элемент лада: {json_key}")
            else:
                print(f"❌ Элемент лада не найден в JSON: {json_key}")

        print(f"📊 Найдено {len(elements)} элементов LAD")
        return elements

    def _is_empty_value(self, value):
        """Проверка на пустое значение"""
        if value is None:
            return True
        if isinstance(value, float) and pd.isna(value):
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        return False

    def validate_barre_data(self, barre_data):
        """Проверка и валидация данных баре"""
        if not barre_data:
            return False

        # Проверяем обязательные поля
        required_fields = ['x', 'y', 'width', 'height']
        for field in required_fields:
            if field not in barre_data:
                print(f"❌ Отсутствует поле {field} в данных баре")
                return False

        return True

    def get_barre_elements(self, bar_value):
        """Получение элементов баре из колонки BAR"""
        elements = []

        if self._is_empty_value(bar_value):
            return elements

        bar_str = str(bar_value).strip()
        print(f"🔍 Поиск баре: '{bar_str}'")

        # Ищем баре в разделе barres
        if bar_str in self.templates.get('barres', {}):
            barre_data = self.templates['barres'][bar_str]

            # Добавляем ключ для идентификации типа
            barre_data['_key'] = bar_str
            barre_data['type'] = 'barre'

            # Валидируем данные баре
            if self.validate_barre_data(barre_data):
                elements.append({
                    'type': 'barre',
                    'data': barre_data
                })
                print(f"✅ Найден баре: {bar_str} - {barre_data.get('width', 0)}x{barre_data.get('height', 0)}")
            else:
                print(f"❌ Невалидные данные баре: {bar_str}")
        else:
            print(f"❌ Баре не найден: {bar_str}")

        return elements

    def get_note_elements_from_column(self, column_value, column_name):
        """Получение элементов нот из колонки с поиском в таблице NOTE"""
        elements = []

        if self._is_empty_value(column_value):
            return elements

        # Преобразуем значение в строку
        note_str = self._convert_value_to_string(column_value)

        # Обрабатываем специальный случай: если значение содержит точку и выглядит как несколько чисел
        # Например: "21.25" может быть "21,25" в Excel
        note_list = self._parse_note_values(note_str)

        print(f"🔍 Поиск элементов для колонки '{column_name}': {note_list}")

        for note_key in note_list:
            print(f"  🔎 Обработка значения: '{note_key}'")

            # Ищем в таблице NOTE
            element_found = self._find_element_in_note_table(note_key, column_name)
            if element_found:
                elements.append(element_found)
                print(f"  ✅ Найден элемент для '{note_key}': {element_found['type']}")
            else:
                print(f"  ❌ Элемент не найден в таблице NOTE для '{note_key}'")

        print(f"📝 Найдено {len(elements)} элементов для колонки '{column_name}'")
        return elements

    def _parse_note_values(self, note_str):
        """Парсит значения нот, обрабатывая специальные случаи с числами"""
        note_str = str(note_str).strip()

        # Сначала пробуем разделить по запятой (нормальный случай)
        if ',' in note_str:
            return [item.strip() for item in note_str.split(',') if item.strip()]

        # Если есть точка и выглядит как несколько чисел (например "21.25" вместо "21,25")
        if '.' in note_str:
            parts = note_str.split('.')
            # Проверяем, может ли это быть несколько целых чисел
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                # Вероятно это "21,25" превратилось в "21.25"
                return [parts[0], parts[1]]
            elif len(parts) > 2 and all(part.isdigit() for part in parts):
                # Множественные числа через точку
                return parts

        # Если ничего не подошло, возвращаем как одно значение
        return [note_str]

    def _convert_value_to_string(self, value):
        """Конвертирует значение в строку, правильно обрабатывая числа с плавающей точкой"""
        if value is None:
            return ""

        if isinstance(value, float):
            # Если число выглядит как целое - преобразуем в int
            if value.is_integer():
                return str(int(value))
            else:
                # Для дробных чисел проверяем, не является ли это несколькими значениями
                str_value = str(value)
                if '.' in str_value:
                    parts = str_value.split('.')
                    # Если после точки 2 цифры и обе части выглядят как отдельные значения
                    if len(parts) == 2 and len(parts[1]) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        # Вероятно это "21,25" -> 21.25
                        return f"{parts[0]}.{parts[1]}"  # Оставляем как есть для дальнейшего парсинга
                return str(value)
        elif isinstance(value, int):
            return str(value)
        else:
            return str(value)

    def _find_element_in_note_table(self, note_key, column_name):
        """Поиск элемента в таблице NOTE по ключу и колонке"""
        if not self.note_data:
            print(f"  ⚠️ Таблица NOTE не загружена, поиск напрямую в JSON")
            return self._find_element_in_json(note_key)

        # Определяем соответствие колонок
        column_mapping = {
            'FNL': ('FNL', 'FNL_ELEM'),
            'FN': ('FN', 'FN_ELEM'),
            'FPOL': ('FPOL', 'FPOL_ELEM'),
            'FPXL': ('FPXL', 'FPXL_ELEM'),
            'FP1': ('FP1', 'FP1_ELEM'),
            'FP2': ('FP2', 'FP2_ELEM'),
            'FP3': ('FP3', 'FP3_ELEM'),
            'FP4': ('FP4', 'FP4_ELEM')
        }

        if column_name not in column_mapping:
            print(f"  ❌ Неизвестная колонка: {column_name}")
            return None

        source_col, elem_col = column_mapping[column_name]

        # Ищем в таблице NOTE
        for note_item in self.note_data:
            item_value = note_item.get(source_col)
            if item_value and not self._is_empty_value(item_value):
                # Конвертируем значение из таблицы для сравнения
                item_value_str = self._convert_value_to_string(item_value)

                # Пробуем разные варианты сравнения
                if self._values_match(item_value_str, note_key):
                    elem_value = note_item.get(elem_col)
                    if elem_value and not self._is_empty_value(elem_value):
                        elem_key = self._convert_value_to_string(elem_value)
                        print(f"  ✅ Найден элемент в NOTE: {note_key} -> {elem_key}")
                        return self._find_element_in_json(elem_key)

        print(f"  ❌ Не найдено соответствие в NOTE для '{note_key}' в колонке '{source_col}'")
        return None

    def _values_match(self, value1, value2):
        """Проверяет, совпадают ли значения с учетом специальных случаев"""
        # Прямое сравнение
        if str(value1).strip() == str(value2).strip():
            return True

        # Если одно значение с точкой, а другое с запятой
        v1_clean = str(value1).replace('.', ',').strip()
        v2_clean = str(value2).replace('.', ',').strip()
        if v1_clean == v2_clean:
            return True

        # Если одно значение целое, а другое дробное с .0
        try:
            v1_float = float(value1)
            v2_float = float(value2)
            if abs(v1_float - v2_float) < 0.001:  # Сравнение с небольшой погрешностью
                return True
        except (ValueError, TypeError):
            pass

        return False

    def _find_element_in_json(self, element_key):
        """Поиск элемента в различных разделах JSON"""
        element_key = element_key.strip()

        # Ищем в notes
        if element_key in self.templates.get('notes', {}):
            element_data = self.templates['notes'][element_key]
            # Добавляем ключ для отладки
            element_data['_key'] = element_key
            element_data['type'] = 'note'  # Явно указываем тип
            print(f"    ✅ Найден элемент ноты: {element_key} (стиль: {element_data.get('style', 'default')})")
            return {
                'type': 'note',
                'data': element_data
            }

        # Ищем в open_notes
        if element_key in self.templates.get('open_notes', {}):
            element_data = self.templates['open_notes'][element_key]
            element_data['_key'] = element_key
            element_data['type'] = 'note'  # Явно указываем тип
            print(f"    ✅ Найден элемент открытой ноты: {element_key} (стиль: {element_data.get('style', 'default')})")
            return {
                'type': 'note',
                'data': element_data
            }

        # Ищем в frets (лады)
        if element_key in self.templates.get('frets', {}):
            element_data = self.templates['frets'][element_key]
            element_data['_key'] = element_key
            element_data['type'] = 'fret'  # Явно указываем тип
            print(f"    ✅ Найден элемент лада: {element_key}")
            return {
                'type': 'fret',
                'data': element_data
            }

        print(f"    ❌ Элемент не найден в JSON: {element_key}")
        return None

    def get_chord_elements(self, chord_config, display_type):
        """Получение элементов аккорда в зависимости от типа отображения"""
        elements = []

        print(f"🎵 Получение элементов для аккорда:")
        print(f"   RAM: {chord_config.get('RAM')}")
        print(f"   BAR: {chord_config.get('BAR')}")
        print(f"   FNL: {chord_config.get('FNL')} (тип: {type(chord_config.get('FNL'))})")
        print(f"   FN: {chord_config.get('FN')} (тип: {type(chord_config.get('FN'))})")
        print(f"   FPOL: {chord_config.get('FPOL')} (тип: {type(chord_config.get('FPOL'))})")
        print(f"   FPXL: {chord_config.get('FPXL')} (тип: {type(chord_config.get('FPXL'))})")
        print(f"   FP1: {chord_config.get('FP1')} (тип: {type(chord_config.get('FP1'))})")
        print(f"   FP2: {chord_config.get('FP2')} (тип: {type(chord_config.get('FP2'))})")
        print(f"   FP3: {chord_config.get('FP3')} (тип: {type(chord_config.get('FP3'))})")
        print(f"   FP4: {chord_config.get('FP4')} (тип: {type(chord_config.get('FP4'))})")

        # Получаем значение LAD из таблицы RAM на основе RAM аккорда
        ram_key = chord_config.get('RAM')
        lad_value = None
        if ram_key:
            lad_value = self.get_ram_lad_value(ram_key)
            print(f"   LAD (из таблицы RAM): {lad_value}")

        # Добавляем RAM элементы из колонки RAM (для обрезки)
        if ram_key:
            ram_elements = self.get_ram_elements(ram_key)
            elements.extend(ram_elements)
            print(f"🔧 Добавлено {len(ram_elements)} элементов RAM")

        # Добавляем LAD элементы на основе значения из таблицы RAM
        if lad_value:
            lad_elements = self.get_ram_elements_from_lad(lad_value)
            elements.extend(lad_elements)
            print(f"🎯 Добавлено {len(lad_elements)} элементов LAD")

        # Добавляем элементы баре ТОЛЬКО для режима пальцев
        if display_type == "fingers":
            bar_elements = self.get_barre_elements(chord_config.get('BAR'))
            elements.extend(bar_elements)
            print(f"🎸 Добавлено {len(bar_elements)} элементов баре")
        else:
            print("🎸 Баре пропущен (режим нот)")

        if display_type == "notes":
            # Для нот: используем FNL и FN
            fnl_elements = self.get_note_elements_from_column(chord_config.get('FNL'), 'FNL')
            fn_elements = self.get_note_elements_from_column(chord_config.get('FN'), 'FN')

            elements.extend(fnl_elements)
            elements.extend(fn_elements)
            print(f"🎵 Добавлено {len(fnl_elements) + len(fn_elements)} элементов нот")

        else:  # fingers
            # Для пальцев: используем FPOL, FPXL, FP1, FP2, FP3, FP4
            fpol_elements = self.get_note_elements_from_column(chord_config.get('FPOL'), 'FPOL')
            fpxl_elements = self.get_note_elements_from_column(chord_config.get('FPXL'), 'FPXL')
            fp1_elements = self.get_note_elements_from_column(chord_config.get('FP1'), 'FP1')
            fp2_elements = self.get_note_elements_from_column(chord_config.get('FP2'), 'FP2')
            fp3_elements = self.get_note_elements_from_column(chord_config.get('FP3'), 'FP3')
            fp4_elements = self.get_note_elements_from_column(chord_config.get('FP4'), 'FP4')

            elements.extend(fpol_elements)
            elements.extend(fpxl_elements)
            elements.extend(fp1_elements)
            elements.extend(fp2_elements)
            elements.extend(fp3_elements)
            elements.extend(fp4_elements)
            print(
                f"👆 Добавлено {len(fpol_elements) + len(fpxl_elements) + len(fp1_elements) + len(fp2_elements) + len(fp3_elements) + len(fp4_elements)} элементов пальцев")

        print(f"📊 ИТОГО элементов для отрисовки: {len(elements)}")

        return elements

    def draw_elements_on_image(self, pixmap, elements, crop_rect=None):
        """Рисование элементов на изображении БЕЗ масштабирования элементов"""
        if pixmap.isNull():
            return pixmap

        result_pixmap = QPixmap(pixmap)
        painter = QPainter(result_pixmap)

        try:
            for element in elements:
                if element['type'] == 'fret':
                    self.draw_fret(painter, element['data'], crop_rect)
                elif element['type'] == 'note':
                    self.draw_note(painter, element['data'], crop_rect)
                elif element['type'] == 'barre':
                    self.draw_barre(painter, element['data'], crop_rect)

        finally:
            painter.end()

        return result_pixmap

    def draw_elements_on_canvas(self, painter, elements, crop_rect):
        """Рисование элементов на готовом QPainter с правильными координатами"""
        try:
            for element in elements:
                if element['type'] == 'fret':
                    self.draw_fret_on_canvas(painter, element['data'], crop_rect)
                elif element['type'] == 'note':
                    self.draw_note_on_canvas(painter, element['data'], crop_rect)
                elif element['type'] == 'barre':
                    self.draw_barre_on_canvas(painter, element['data'], crop_rect)
        except Exception as e:
            print(f"❌ Ошибка рисования элементов на canvas: {e}")
            import traceback
            traceback.print_exc()

    def draw_fret(self, painter, fret_data, crop_rect=None):
        """Рисование лада с учетом обрезки"""
        try:
            # Адаптируем координаты к обрезанному изображению
            adapted_data = self._adapt_coordinates_simple(fret_data, crop_rect)
            symbol = adapted_data.get('symbol', '?')
            print(f"🎨 Рисование лада: {symbol} на позиции ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)})")

            from drawing_elements import DrawingElements
            DrawingElements.draw_fret(painter, adapted_data)
        except Exception as e:
            print(f"❌ Ошибка рисования лада: {e}")

    def draw_fret_on_canvas(self, painter, fret_data, crop_rect):
        """Рисование лада на canvas с правильными координатами"""
        try:
            # Адаптируем координаты к canvas
            adapted_data = self._adapt_coordinates_for_canvas(fret_data, crop_rect)
            symbol = adapted_data.get('symbol', '?')
            print(
                f"🎨 Рисование лада на canvas: {symbol} на позиции ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)})")

            from drawing_elements import DrawingElements
            DrawingElements.draw_fret(painter, adapted_data)
        except Exception as e:
            print(f"❌ Ошибка рисования лада на canvas: {e}")

    def draw_note(self, painter, note_data, crop_rect=None):
        """Рисование ноты с учетом обрезки"""
        try:
            # Адаптируем координаты к обрезанному изображению
            adapted_data = self._adapt_coordinates_simple(note_data, crop_rect)

            # Определяем тип отображаемого текста
            display_text = adapted_data.get('display_text', 'finger')
            if display_text == 'note_name':
                symbol = adapted_data.get('note_name', '')
            elif display_text == 'symbol':
                symbol = adapted_data.get('symbol', '')
            else:  # finger
                symbol = adapted_data.get('finger', '1')

            print(f"🎵 Рисование ноты: {symbol} на позиции ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)}) "
                  f"стиль: {adapted_data.get('style', 'default')}")

            from drawing_elements import DrawingElements
            DrawingElements.draw_note(painter, adapted_data)
        except Exception as e:
            print(f"Ошибка рисования ноты: {e}")

    def draw_note_on_canvas(self, painter, note_data, crop_rect):
        """Рисование ноты на canvas с правильными координатами"""
        try:
            # Адаптируем координаты к canvas
            adapted_data = self._adapt_coordinates_for_canvas(note_data, crop_rect)

            # Определяем тип отображаемого текста
            display_text = adapted_data.get('display_text', 'finger')
            if display_text == 'note_name':
                symbol = adapted_data.get('note_name', '')
            elif display_text == 'symbol':
                symbol = adapted_data.get('symbol', '')
            else:  # finger
                symbol = adapted_data.get('finger', '1')

            print(
                f"🎵 Рисование ноты на canvas: {symbol} на позиции ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)}) "
                f"стиль: {adapted_data.get('style', 'default')}")

            from drawing_elements import DrawingElements
            DrawingElements.draw_note(painter, adapted_data)
        except Exception as e:
            print(f"Ошибка рисования ноты на canvas: {e}")

    def draw_barre(self, painter, barre_data, crop_rect=None):
        """Рисование баре с учетом обрезки - ПРОСТОЙ СДВИГ КООРДИНАТ"""
        try:
            # Адаптируем координаты к обрезанному изображению
            adapted_data = self._adapt_coordinates_simple(barre_data, crop_rect)

            print(f"🎸 Рисование баре: позиция ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)}) "
                  f"размер {adapted_data.get('width', 0)}x{adapted_data.get('height', 0)} "
                  f"стиль {adapted_data.get('style', 'default')}")

            from drawing_elements import DrawingElements
            DrawingElements.draw_barre(painter, adapted_data)
        except Exception as e:
            print(f"❌ Ошибка рисования баре: {e}")
            import traceback
            traceback.print_exc()

    def draw_barre_on_canvas(self, painter, barre_data, crop_rect):
        """Рисование баре на canvas с правильными координатами"""
        try:
            # Адаптируем координаты к canvas
            adapted_data = self._adapt_coordinates_for_canvas(barre_data, crop_rect)

            print(f"🎸 Рисование баре на canvas: позиция ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)}) "
                  f"размер {adapted_data.get('width', 0)}x{adapted_data.get('height', 0)} "
                  f"радиус {adapted_data.get('radius', 0)}")

            from drawing_elements import DrawingElements
            DrawingElements.draw_barre(painter, adapted_data)
        except Exception as e:
            print(f"❌ Ошибка рисования баре на canvas: {e}")
            import traceback
            traceback.print_exc()

    def _adapt_coordinates_simple(self, element_data, crop_rect):
        """Простая адаптация координат - только сдвиг без масштабирования"""
        if not crop_rect:
            return element_data.copy()

        # Копируем данные элемента
        adapted_data = element_data.copy()

        # Получаем координаты обрезки
        crop_x, crop_y, crop_width, crop_height = crop_rect

        # Просто вычитаем координаты обрезки
        if 'x' in adapted_data:
            adapted_data['x'] = adapted_data['x'] - crop_x

        if 'y' in adapted_data:
            adapted_data['y'] = adapted_data['y'] - crop_y

        # Преобразуем в целые числа для Qt
        adapted_data['x'] = int(round(adapted_data.get('x', 0)))
        adapted_data['y'] = int(round(adapted_data.get('y', 0)))

        if 'width' in adapted_data:
            adapted_data['width'] = int(round(adapted_data.get('width', 100)))
        if 'height' in adapted_data:
            adapted_data['height'] = int(round(adapted_data.get('height', 20)))
        if 'radius' in adapted_data:
            adapted_data['radius'] = int(round(adapted_data.get('radius', 10)))

        return adapted_data

    def _adapt_coordinates_for_canvas(self, element_data, crop_rect):
        """Упрощенная адаптация координат для canvas - ВСЕ элементы одинаково"""
        if not crop_rect:
            return element_data.copy()

        # Копируем данные элемента
        adapted_data = element_data.copy()

        # Получаем координаты обрезки
        crop_x, crop_y, crop_width, crop_height = crop_rect

        original_x = element_data.get('x', 0)
        original_y = element_data.get('y', 0)

        print(f"🎯 Адаптация {element_data.get('type', 'unknown')}:")
        print(f"   Оригинальные координаты: ({original_x}, {original_y})")
        print(f"   Область обрезки: ({crop_x}, {crop_y}, {crop_width}, {crop_height})")

        # Для ВСЕХ элементов просто вычитаем координаты обрезки
        if 'x' in adapted_data:
            adapted_data['x'] = original_x - crop_x

        if 'y' in adapted_data:
            adapted_data['y'] = original_y - crop_y

        # Преобразуем в целые числа для Qt
        adapted_data['x'] = int(round(adapted_data.get('x', 0)))
        adapted_data['y'] = int(round(adapted_data.get('y', 0)))

        # Для баре - дополнительная коррекция координат (центр -> левый верхний угол)
        if adapted_data.get('type') == 'barre':
            barre_width = adapted_data.get('width', 100)
            barre_height = adapted_data.get('height', 20)

            if 'x' in adapted_data:
                adapted_data['x'] = adapted_data['x'] - (barre_width // 2)
            if 'y' in adapted_data:
                adapted_data['y'] = adapted_data['y'] - (barre_height // 2)

        print(f"   Финальные координаты: ({adapted_data.get('x', 0)}, {adapted_data.get('y', 0)})")

        return adapted_data

    def get_brush_from_style(self, style_name, x=0, y=0, radius=0, width=0, height=0):
        """Получение кисти на основе стиля с поддержкой градиентов"""
        if style_name == "wood":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(210, 180, 140))
            gradient.setColorAt(0.5, QColor(160, 120, 80))
            gradient.setColorAt(1, QColor(210, 180, 140))
            return QBrush(gradient)
        elif style_name == "metal":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(200, 200, 200))
            gradient.setColorAt(0.5, QColor(100, 100, 100))
            gradient.setColorAt(1, QColor(200, 200, 200))
            return QBrush(gradient)
        elif style_name == "rubber":
            gradient = QRadialGradient(x + width / 2, y + height / 2, max(width, height))
            gradient.setColorAt(0, QColor(80, 80, 80))
            gradient.setColorAt(1, QColor(40, 40, 40))
            return QBrush(gradient)
        elif style_name == "gradient":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(189, 183, 107))
            lighter = QColor(189, 183, 107).lighter(150)
            gradient.setColorAt(1, QColor(lighter.red(), lighter.green(), lighter.blue()))
            return QBrush(gradient)
        elif style_name == "striped":
            return QBrush(QColor(189, 183, 107))

        # НОВЫЕ ОРАНЖЕВЫЕ СТИЛИ ДЛЯ БАРЕ (ТАКИЕ ЖЕ КАК В drawing_elements.py)
        elif style_name == "orange_gradient":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 200, 100))  # Светло-оранжевый
            gradient.setColorAt(0.5, QColor(255, 140, 0))  # Оранжевый
            gradient.setColorAt(1, QColor(255, 100, 0))  # Темно-оранжевый
            return QBrush(gradient)
        elif style_name == "orange_metal":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 220, 150))
            gradient.setColorAt(0.3, QColor(255, 180, 80))
            gradient.setColorAt(0.7, QColor(255, 140, 40))
            gradient.setColorAt(1, QColor(255, 120, 20))
            return QBrush(gradient)
        elif style_name == "orange_glow":
            gradient = QRadialGradient(x + width / 2, y + height / 2, max(width, height) * 0.8)
            gradient.setColorAt(0, QColor(255, 230, 180))
            gradient.setColorAt(0.5, QColor(255, 180, 80))
            gradient.setColorAt(1, QColor(255, 140, 0))
            return QBrush(gradient)
        elif style_name == "dark_orange":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 150, 50))
            gradient.setColorAt(0.5, QColor(255, 120, 0))
            gradient.setColorAt(1, QColor(220, 100, 0))
            return QBrush(gradient)
        elif style_name == "orange_wood":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 200, 150))
            gradient.setColorAt(0.3, QColor(255, 170, 100))
            gradient.setColorAt(0.7, QColor(255, 140, 60))
            gradient.setColorAt(1, QColor(255, 120, 40))
            return QBrush(gradient)
        elif style_name == "bright_orange":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 230, 100))
            gradient.setColorAt(0.5, QColor(255, 200, 0))
            gradient.setColorAt(1, QColor(255, 160, 0))
            return QBrush(gradient)
        elif style_name == "orange_red":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 180, 100))
            gradient.setColorAt(0.5, QColor(255, 120, 0))
            gradient.setColorAt(1, QColor(255, 80, 0))
            return QBrush(gradient)
        elif style_name == "orange_yellow":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 240, 150))
            gradient.setColorAt(0.5, QColor(255, 200, 50))
            gradient.setColorAt(1, QColor(255, 180, 0))
            return QBrush(gradient)
        elif style_name == "orange_brown":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 190, 130))
            gradient.setColorAt(0.5, QColor(255, 150, 80))
            gradient.setColorAt(1, QColor(210, 120, 60))
            return QBrush(gradient)
        elif style_name == "orange_pastel":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 220, 180))
            gradient.setColorAt(0.5, QColor(255, 190, 140))
            gradient.setColorAt(1, QColor(255, 170, 120))
            return QBrush(gradient)

        # Стиль по умолчанию
        return QBrush(QColor(189, 183, 107))  # Золотистый по умолчанию