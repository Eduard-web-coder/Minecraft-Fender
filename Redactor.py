import re
import sys
import subprocess
import time
import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QIcon, QTextCursor, QFont, QSyntaxHighlighter,
    QTextCharFormat, QColor
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QAction, QSplitter, QInputDialog
)

class BatSyntaxHighlighter(QSyntaxHighlighter):
    """
    Пример простого подсветчика синтаксиса для Batch (BAT) файлов.
    Правила можно расширять или редактировать при необходимости.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []

        # Формат для ключевых слов (команд)
        commandFormat = QTextCharFormat()
        commandFormat.setForeground(QColor("#ffaa00"))  # оранжевый цвет

        commands = [
            r"\becho\b", r"\bset\b", r"\bif\b", r"\bgoto\b", r"\bexit\b",
            r"\bstart\b", r"\btitle\b", r"\bcolor\b", r"\bcls\b", r"\bpause\b",
            r"\bcd\b", r"\bdir\b", r"\bcopy\b", r"\bmove\b", r"\bdel\b", r"\bxcopy\b"
        ]
        # Добавляем правила для ключевых слов
        for cmd in commands:
            pattern = re.compile(cmd, re.IGNORECASE)
            self.highlightingRules.append((pattern, commandFormat))

        # Формат для комментариев (REM / ::)
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor("#00ff00"))  # зеленый цвет

        # Правило для строк, начинающихся с REM (учитывая возможный @) и для строк, начинающихся с ::
        self.highlightingRules.append((re.compile(r"^\s*@?[Rr][Ee][Mm].*"), commentFormat))
        self.highlightingRules.append((re.compile(r"^\s*::.*"), commentFormat))

        # Формат для переменных окружения вида %VAR%
        varFormat = QTextCharFormat()
        varFormat.setForeground(QColor("#ffff00"))  # желтый цвет
        self.highlightingRules.append((re.compile(r"%[A-Za-z0-9_]+%"), varFormat))

    def highlightBlock(self, text):
        """
        Переопределяем метод, чтобы применить все правила подсветки к строке.
        """
        for pattern, fmt in self.highlightingRules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)
        self.setCurrentBlockState(0)


class ScriptBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BAT Script Editor")
        self.setGeometry(100, 100, 1100, 500)
        self.setWindowIcon(QIcon("Terminal.png"))
        
        self.unsaved_changes = False
        self.last_opened_file = None
        self.recent_files = []
        self.dark_mode = False
        self.default_font_size = 12
        
        # Создание редактора кода
        self.code_area = QTextEdit(self)
        self.code_area.setPlaceholderText("Ваш скрипт...")
        self.code_area.textChanged.connect(self.on_text_changed)
        self.code_area.setFont(QFont("Consolas", 12))

        # Подключаем наш подсветчик синтаксиса к документу QTextEdit
        self.highlighter = BatSyntaxHighlighter(self.code_area.document())
        
        # Создание вкладок с командами
        self.command_tabs = QTabWidget(self)
        self.create_command_tabs()
        
        # QSplitter для разделения редактора и вкладок команд
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.code_area)
        splitter.addWidget(self.command_tabs)
        splitter.setSizes([800, 300])
        
        # Панель с кнопками приложения (сверху над QSplitter)
        top_panel = self.create_top_buttons_panel()
        
        # Основной виджет: сверху панель кнопок, затем QSplitter
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_panel)
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Создание меню и статус-бара
        self.create_menubar()
        self.statusBar().showMessage("V.2.4.5")
        
        self.setStyle()
        self.create_shortcuts()
        self.create_recent_files_menu()
    
    def create_top_buttons_panel(self):
        panel = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Кнопка "Сохранить" с иконкой Save.png
        save_button = QPushButton("Сохранить")
        save_button.setIcon(QIcon("Save.png"))
        save_button.clicked.connect(self.save_file)
        layout.addWidget(save_button)
        
        # Кнопка "Сохранить и тестировать" с иконкой Play.png
        save_run_button = QPushButton("Сохранить и тестировать")
        save_run_button.setIcon(QIcon("Play.png"))
        save_run_button.clicked.connect(self.save_and_run_script)
        layout.addWidget(save_run_button)
        
        # Кнопка "Редактировать выбранный файл" с иконкой Edit.png
        edit_button = QPushButton("Редактировать выбранный файл")
        edit_button.setIcon(QIcon("Edit.png"))
        edit_button.clicked.connect(self.edit_selected_bat)
        layout.addWidget(edit_button)
        
        # Кнопка "Выход" с иконкой Exit.png
        exit_button = QPushButton("Выход")
        exit_button.setIcon(QIcon("Exit.png"))
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button)
        
        panel.setLayout(layout)
        return panel

    def create_menubar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("Новый", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        save_run_action = QAction("Сохранить и запустить", self)
        save_run_action.setShortcut("Ctrl+T")
        save_run_action.triggered.connect(self.save_and_run_script)
        file_menu.addAction(save_run_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Правка")
        
        undo_action = QAction("Отменить", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.code_area.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Повторить", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.code_area.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Вырезать", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.code_area.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Копировать", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.code_area.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Вставить", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.code_area.paste)
        edit_menu.addAction(paste_action)
        
        select_all_action = QAction("Выделить всё", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.code_area.selectAll)
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        clear_action = QAction("Очистить редактор", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_editor)
        edit_menu.addAction(clear_action)
        
        find_action = QAction("Найти", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_text)
        edit_menu.addAction(find_action)
        
        find_replace_action = QAction("Найти и заменить", self)
        find_replace_action.setShortcut("Ctrl+R")
        find_replace_action.triggered.connect(self.find_and_replace)
        edit_menu.addAction(find_replace_action)
        
        insert_datetime_action = QAction("Вставить дату/время", self)
        insert_datetime_action.setShortcut("Ctrl+D")
        insert_datetime_action.triggered.connect(self.insert_date_time)
        edit_menu.addAction(insert_datetime_action)

        duplicate_line_action = QAction("Дублировать строку", self)
        duplicate_line_action.setShortcut("Ctrl+D")
        duplicate_line_action.triggered.connect(self.duplicate_line)
        edit_menu.addAction(duplicate_line_action)

        comment_uncomment_action = QAction("Комментировать/Раскомментировать", self)
        comment_uncomment_action.setShortcut("Ctrl+/")
        comment_uncomment_action.triggered.connect(self.comment_uncomment)
        edit_menu.addAction(comment_uncomment_action)

        increase_font_size_action = QAction("Увеличить размер шрифта", self)
        increase_font_size_action.setShortcut("Ctrl++")
        increase_font_size_action.triggered.connect(self.increase_font_size)
        edit_menu.addAction(increase_font_size_action)

        decrease_font_size_action = QAction("Уменьшить размер шрифта", self)
        decrease_font_size_action.setShortcut("Ctrl+-")
        decrease_font_size_action.triggered.connect(self.decrease_font_size)
        edit_menu.addAction(decrease_font_size_action)

        reset_font_size_action = QAction("Сбросить размер шрифта", self)
        reset_font_size_action.setShortcut("Ctrl+0")
        reset_font_size_action.triggered.connect(self.reset_font_size)
        edit_menu.addAction(reset_font_size_action)

        convert_to_uppercase_action = QAction("Преобразовать в верхний регистр", self)
        convert_to_uppercase_action.setShortcut("Ctrl+U")
        convert_to_uppercase_action.triggered.connect(self.convert_to_uppercase)
        edit_menu.addAction(convert_to_uppercase_action)

        convert_to_lowercase_action = QAction("Преобразовать в нижний регистр", self)
        convert_to_lowercase_action.setShortcut("Ctrl+L")
        convert_to_lowercase_action.triggered.connect(self.convert_to_lowercase)
        edit_menu.addAction(convert_to_lowercase_action)

        insert_template_action = QAction("Вставить шаблон", self)
        insert_template_action.setShortcut("Ctrl+T")
        insert_template_action.triggered.connect(self.insert_template)
        edit_menu.addAction(insert_template_action)

        toggle_word_wrap_action = QAction("Переключить перенос слов", self)
        toggle_word_wrap_action.setShortcut("Ctrl+W")
        toggle_word_wrap_action.triggered.connect(self.toggle_word_wrap)
        edit_menu.addAction(toggle_word_wrap_action)

        count_lines_action = QAction("Подсчитать строки", self)
        count_lines_action.setShortcut("Ctrl+Shift+L")
        count_lines_action.triggered.connect(self.count_lines)
        edit_menu.addAction(count_lines_action)
        
        view_menu = menubar.addMenu("Вид")
        dark_mode_action = QAction("Темный режим", self, checkable=True)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        help_menu = menubar.addMenu("Помощь")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setStyle(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2c3e50; }
            QMenuBar { background-color: #34495e; color: #ecf0f1; }
            QMenuBar::item { background-color: #34495e; padding: 6px 12px; }
            QMenuBar::item:selected { background-color: #3d566e; }
            QMenu { background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; }
            QMenu::item:selected { background-color: #3d566e; }
            QTextEdit { 
                background-color: #1e272e; 
                color: #ecf0f1; 
                border: 2px solid #34495e; 
                border-radius: 8px; 
                padding: 8px; 
            }
            QTabWidget::pane { 
                border: 2px solid #34495e; 
                border-radius: 8px; 
                margin: 5px; 
            }
            QTabBar::tab { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3d566e, stop:1 #34495e); 
                color: #ecf0f1; 
                padding: 10px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                margin: 2px;
            }
            QTabBar::tab:selected { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a6984, stop:1 #3d566e);
            }
            QPushButton { 
                background-color: #3d566e; 
                color: #ecf0f1; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px; 
            }
            QPushButton:hover { 
                background-color: #4a6984; 
            }
        """)
    
    def create_shortcuts(self):
        # Дополнительные горячие клавиши уже заданы в меню
        pass
    
    def on_text_changed(self):
        self.unsaved_changes = True
    
    def confirm_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Сохранить изменения?",
                "У вас есть несохраненные изменения. Сохранить их?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.save_file()
                return True
            elif reply == QMessageBox.No:
                return True
            else:
                return False
        return True

    def new_file(self):
        if self.confirm_unsaved_changes():
            self.code_area.clear()
            self.last_opened_file = None
            self.unsaved_changes = False
            self.statusBar().showMessage("Новый файл создан.")

    def open_file(self):
        if self.confirm_unsaved_changes():
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Открыть BAT файл", "", "Batch Files (*.bat);;All Files (*)", options=options
            )
            if file_name:
                try:
                    with open(file_name, "r", encoding="utf-8") as file:
                        self.code_area.setText(file.read())
                    self.last_opened_file = file_name
                    self.unsaved_changes = False
                    self.statusBar().showMessage(f"Открыт файл: {file_name}")
                    self.add_to_recent_files(file_name)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def closeEvent(self, event):
        if self.confirm_unsaved_changes():
            event.accept()
        else:
            event.ignore()
    
    def save_file(self):
        if self.last_opened_file:
            self._save_to_file(self.last_opened_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Сохранить скрипт", self.last_opened_file or "",
            "Batch Files (*.bat);;All Files (*)", options=options
        )
        if file_name:
            self._save_to_file(file_name)
    
    def _save_to_file(self, file_name):
        try:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self.code_area.toPlainText())
            self.unsaved_changes = False
            self.last_opened_file = file_name
            self.statusBar().showMessage(f"Сохранено: {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
    
    def save_and_run_script(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Сохранить и запустить", self.last_opened_file or "",
            "Batch Files (*.bat);;All Files (*)", options=options
        )
        if file_name:
            try:
                with open(file_name, "w", encoding="utf-8") as file:
                    file.write(self.code_area.toPlainText())
                self.unsaved_changes = False
                self.last_opened_file = file_name
                self.statusBar().showMessage(f"Сохранено и запущено: {file_name}")
                time.sleep(0.5)
                subprocess.Popen(f'start cmd /k "{file_name}"', shell=True)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить или запустить файл:\n{e}")
    
    def edit_selected_bat(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Открыть BAT файл для редактирования", self.last_opened_file or "",
            "Batch Files (*.bat);;All Files (*)", options=options
        )
        if file_name:
            try:
                with open(file_name, "r", encoding="utf-8") as file:
                    self.code_area.setText(file.read())
                self.last_opened_file = file_name
                self.statusBar().showMessage(f"Редактирование файла: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def clear_editor(self):
        self.code_area.clear()
        self.unsaved_changes = False
        self.statusBar().showMessage("Редактор очищен.")
    
    def find_text(self):
        text, ok = QInputDialog.getText(self, "Найти", "Введите текст для поиска:")
        if ok and text:
            # Ищем первое вхождение
            if not self.code_area.find(text):
                # Если не нашли, перемещаем курсор в начало и ищем снова
                cursor = self.code_area.textCursor()
                cursor.movePosition(QTextCursor.Start)
                self.code_area.setTextCursor(cursor)
                if not self.code_area.find(text):
                    QMessageBox.information(self, "Найти", "Текст не найден.")
    
    def find_and_replace(self):
        find_text, ok = QInputDialog.getText(self, "Найти", "Введите текст для поиска:")
        if ok and find_text:
            replace_text, ok = QInputDialog.getText(self, "Заменить", "Введите текст для замены:")
            if ok:
                cursor = self.code_area.textCursor()
                cursor.beginEditBlock()
                doc = self.code_area.document()
                pos = 0
                while True:
                    pos = doc.toPlainText().find(find_text, pos)
                    if pos == -1:
                        break
                    cursor.setPosition(pos)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(find_text))
                    cursor.insertText(replace_text)
                    pos += len(replace_text)
                cursor.endEditBlock()
    
    def insert_date_time(self):
        current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.code_area.insertPlainText(current_dt)
    
    def show_about(self):
        QMessageBox.about(
            self, "О программе",
            "BAT Script Editor\nВерсия 2.4.5.\nРазработано поставщиком ПО"
        )
    
    def create_command_tabs(self):
        file_commands = ["append", "assoc", "attrib", "copy", "del", "move", "rename", "xcopy", "mkdir", "rmdir"]
        network_commands = ["arp", "getmac", "ipconfig", "netsh", "ping", "tracert", "ftp", "netstat"]
        system_commands = ["bootcfg", "chkdsk", "color", "date", "echo", "exit", "shutdown", "systeminfo"]
        misc_commands = [
            "curl ascii.live/rick",
            "curl http://artscene.textfiles.com/vt100/movglobe.vt",
            "pause",
            "help",
            "ver",
            "time",
            "title",
            "cls"
        ]
        
        self.create_command_tab("Файловые", file_commands)
        self.create_command_tab("Сетевые", network_commands)
        self.create_command_tab("Системные", system_commands)
        self.create_command_tab("Прочее", misc_commands)
    
    def create_command_tab(self, tab_name, commands):
        tab = QWidget()
        layout = QVBoxLayout()
        for command in commands:
            self.create_button(layout, command, command)
        layout.addStretch()
        tab.setLayout(layout)
        self.command_tabs.addTab(tab, tab_name)
    
    def create_button(self, layout, text, command):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.add_code(command))
        layout.addWidget(button)
    
    def add_code(self, code):
        self.code_area.append(code)
        self.code_area.moveCursor(QTextCursor.End)
    
    def create_recent_files_menu(self):
        self.recent_files_menu = self.menuBar().addMenu("Недавние файлы")
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_files_menu.clear()
        for file_name in self.recent_files:
            action = QAction(file_name, self)
            action.triggered.connect(lambda checked, file_name=file_name: self.open_recent_file(file_name))
            self.recent_files_menu.addAction(action)

    def open_recent_file(self, file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                self.code_area.setText(file.read())
            self.last_opened_file = file_name
            self.unsaved_changes = False
            self.statusBar().showMessage(f"Открыт файл: {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def add_to_recent_files(self, file_name):
        if file_name not in self.recent_files:
            self.recent_files.insert(0, file_name)
            if len(self.recent_files) > 5:
                self.recent_files.pop()
        self.update_recent_files_menu()

    def toggle_dark_mode(self):
        if self.dark_mode:
            self.setStyleSheet("")
            self.dark_mode = False
        else:
            self.setStyle()
            self.dark_mode = True

    def duplicate_line(self):
        cursor = self.code_area.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        line_text = cursor.selectedText()
        cursor.movePosition(QTextCursor.EndOfLine)
        cursor.insertText("\n" + line_text)
    
    def comment_uncomment(self):
        cursor = self.code_area.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.StartOfLine)
            while cursor.position() < end:
                cursor.insertText("REM ")
                cursor.movePosition(QTextCursor.Down)
                cursor.movePosition(QTextCursor.StartOfLine)
                end += 4
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            line_text = cursor.selectedText()
            if line_text.strip().startswith("REM"):
                cursor.removeSelectedText()
                cursor.insertText(line_text[4:])
            else:
                cursor.insertText("REM " + line_text)
        cursor.endEditBlock()

    def increase_font_size(self):
        font = self.code_area.font()
        font.setPointSize(font.pointSize() + 1)
        self.code_area.setFont(font)

    def decrease_font_size(self):
        font = self.code_area.font()
        font.setPointSize(font.pointSize() - 1)
        self.code_area.setFont(font)

    def reset_font_size(self):
        font = self.code_area.font()
        font.setPointSize(self.default_font_size)
        self.code_area.setFont(font)

    def convert_to_uppercase(self):
        cursor = self.code_area.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(selected_text.upper())

    def convert_to_lowercase(self):
        cursor = self.code_area.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(selected_text.lower())

    def insert_template(self):
        template = "@echo off\nREM This is a template\n"
        self.code_area.insertPlainText(template)

    def toggle_word_wrap(self):
        if self.code_area.lineWrapMode() == QTextEdit.NoWrap:
            self.code_area.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.code_area.setLineWrapMode(QTextEdit.NoWrap)

    def count_lines(self):
        line_count = self.code_area.document().blockCount()
        QMessageBox.information(self, "Line Count", f"Number of lines: {line_count}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptBuilder()
    window.show()
    sys.exit(app.exec_())
