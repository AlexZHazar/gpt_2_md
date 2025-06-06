# pip install PySide6 html2text requests chardet

"""
Web to Markdown Converter using PySide6

1. save ChatGPT conversations as MHTML
2. convert MHTML to Markdown by this app

"""
import os
import re
import sys
from datetime import datetime
from configparser import ConfigParser
import quopri
import chardet
import html2text
from email import policy
from email.parser import BytesParser

from pprint import pprint

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QLabel, QCheckBox, QGroupBox
)


CONFIG_PATH = "config.ini"


def load_config():
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        config.write(f)


class WebToMarkdownApp(QWidget):
    def __init__(self):
        super().__init__()

        self.md_text = ""
        self.file_path = ""
        self.now = None
        self.page_groups = []

        self.setWindowTitle("MHTML → Markdown")
        self.config = load_config()

        self.load_file_button = QPushButton("Открыть MHTML файл")
        self.mhtml_path_label = QLabel("")

        self.split_pages_cb = QCheckBox("Разбить по страницам")
        self.page_name_template = QLineEdit("page")
        self.range_input = QLineEdit()
        self.path_label = QLabel("Путь не выбран")
        self.choose_btn = QPushButton("Указать папку сохранения")
        self.save_btn = QPushButton("Сохранить")

        # === Группа "Параметры экспорта"
        group_box_export = QGroupBox("Параметры экспорта")
        group_layout_export = QVBoxLayout(group_box_export)

        # === Группа "Параметры экспорта"
        group_box_pages = QGroupBox("Укажите номера страниц, которые нужно сохранить")
        group_layout_pages = QVBoxLayout(group_box_pages)

        group_layout_pages.addWidget(QLabel("Оставьте поле ниже пустым для формирования всех страниц"))
        group_layout_pages.addWidget(QLabel("Пример диапазонов (группировка и пересечения возможны):    (1,4),5,(8,11-13),15-18,6-9"))
        group_layout_pages.addWidget(self.range_input)

        group_layout_export.addWidget(self.split_pages_cb)
        group_layout_export.addWidget(QLabel())
        group_layout_export.addWidget(QLabel("Укажите шаблон имени страницы по правилам именования файлов:"))
        group_layout_export.addWidget(self.page_name_template)
        group_layout_export.addWidget(QLabel())
        group_layout_export.addWidget(group_box_pages)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.load_file_button)
        self.layout.addWidget(self.mhtml_path_label)

        self.layout.addWidget(QLabel())

        self.layout.addWidget(group_box_export)

        self.layout.addWidget(QLabel())

        self.layout.addWidget(self.path_label)
        self.layout.addWidget(self.choose_btn)
        self.layout.addWidget(self.save_btn)

        self.setLayout(self.layout)

        self.load_file_button.clicked.connect(self.handle_mhtml)

        self.choose_btn.clicked.connect(self.choose_folder)
        self.save_btn.clicked.connect(self.save)
        self.split_pages_cb.stateChanged.connect(self.on_checkbox_toggled)

        # set default path from config
        default_path = self.config.get("Settings", "default_path", fallback=".")
        self.export_path = default_path
        self.path_label.setText("Путь к проекту Obsidian: "+default_path)

        self.activate_all_widgets(self, False)

    def on_checkbox_toggled(self, checked: bool):
        if checked:
            self.range_input.setEnabled(True)
            self.page_name_template.setEnabled(True)
        else:
            self.range_input.setEnabled(False)
            self.page_name_template.setEnabled(False)
        # print("✅" if checked else "❌")

    def activate_all_widgets(self, parent: QWidget, status: bool = True):
        for widget in parent.findChildren(QWidget, options=Qt.FindChildrenRecursively):
            widget.setEnabled(status)
            self.load_file_button.setEnabled(True)
        if status:
            self.range_input.setEnabled(False)
            self.page_name_template.setEnabled(False)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Укажите путь к проекту Obsidian", self.export_path)
        if folder:
            self.export_path = folder
            self.path_label.setText("Путь к проекту Obsidian: "+folder)
            self.config.set("Settings", "default_path", folder)
            save_config(self.config)

    @staticmethod
    def parse_page_groups(text: str) -> list[list[int]]:
        text = text.replace(' ', '')
        groups = []

        # Поиск скобочных групп
        pattern = r'\((.*?)\)|([^,()]+)'
        matches = re.findall(pattern, text)

        for group_str, single in matches:
            raw = group_str if group_str else single
            items = raw.split(',')

            group = set()
            for item in items:
                if '-' in item:
                    start, end = item.split('-')
                    group.update(range(int(start), int(end) + 1))
                elif item:
                    group.add(int(item))
            groups.append(sorted(group))

        # groups_enum = list(enumerate(groups))
        # print(groups)
        # print(groups_enum)

        return groups

    @staticmethod
    def get_line(text: str, line_n: int = 2, max_length: int = 80) -> str:
        lines = text.splitlines()
        if len(lines) >= line_n + 1:
            return lines[line_n][:max_length]
        return ""

    def save(self):
        page = self.page_name_template.text()
        page = 'page' if page.strip()=='' else page
        self.now = datetime.now().strftime("%Y%m%d%H%M%S")
        base_path = self.export_path
        if self.split_pages_cb.isChecked():
            base_path = os.path.join(base_path, f"exported_{self.now}")
            os.makedirs(base_path, exist_ok=True)
            blocks = self.split_text(self.md_text)
            with open(os.path.join(base_path, "headers.md"), "w", encoding="utf-8") as f:
                f.writelines('\n')
                for idx, block in enumerate(blocks):
                    blocks[idx] = str(idx+1)+"\n"+block
                    f.writelines(f"[[exported_{self.now}/{page} {idx+1:03}|{idx+1}]]      {idx + 1}\n{self.get_line(block)}"+"\n"*2)

            merged = self.merge_blocks(blocks)
            if self.range_input.text().strip():
                with open(os.path.join(base_path, "headers.md"), "w", encoding="utf-8") as f:
                    f.writelines('\n')
                    for m_idx, m_block in enumerate(merged):
                        f.writelines(f"%%  Запросы:  {', '.join(str(x) for x in self.page_groups[m_idx])}  %%\n")
                        f.writelines(f"[[exported_{self.now}/{page} {m_idx+1:03}|{m_idx+1}]]      {m_idx + 1}\n{self.get_line(m_block[0], 3)}"+"\n"*2)
            self.save_blocks(merged, base_path)
        else:
            file_path = os.path.join(base_path, f"exported_file_{self.now}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.md_text)
            QMessageBox.information(self, "Готово", f"Сохранено в: {file_path}")

    def split_text(self, text):
        text = re.sub(r'[>] \[!important\] Запрос:', 's'*50+'> [!important] Запрос:', text, flags=re.DOTALL | re.MULTILINE)
        return re.split('s'*50, text)[1:]

    def merge_blocks(self, blocks: list[str]) -> list[list[str]]:
        if not self.range_input.text().strip():
            return [[block.strip()] for block in blocks]

        self.page_groups = self.parse_page_groups(self.range_input.text())
        merged = []

        for group in self.page_groups:
            merged_group = []
            for i in group:
                if 1 <= i <= len(blocks):
                    merged_group.append(blocks[i - 1].strip())
            merged.append(merged_group)

        return merged

    def save_blocks(self, merged_blocks, base_path):
        page = self.page_name_template.text()
        page = 'page' if page.strip()=='' else page
        tag_string_len = int(self.config.get("Settings", "tag_string_len", fallback=""))
        # keywords = self.config.get("Keywords", "words", fallback="").split(',')

        raw_value = self.config.get("Keywords", "words", fallback="")
        keywords = [line.strip() for line in raw_value.strip().splitlines() if line.strip()]
        keywords = self.convert_tags(keywords)
        # pprint(keywords)
        # print(keywords)
        for idx, group in enumerate(merged_blocks):
            content = "\n\n".join(group)
            print(content)
            print('='*100)
            filename = f"{page} {idx+1:03}.md"
            prev_link = f"[[exported_{self.now}/{page} {idx:03}|{page} {idx:03}]]  <"+" "*10 if idx > 0 else ""
            header_link = f"[[exported_{self.now}/headers.md|headers]]"+" "*10
            next_link = f">  [[exported_{self.now}/{page} {idx+2:03}|{page} {idx+2:03}]]" if idx < len(merged_blocks) - 1 else ""
            # range_info = f"\n%%  Запросы: {self.range_input.text().strip()}  %%\n" if self.range_input.text().replace('%', '').strip() else ""

            range_info = f"\n%%  Запросы:  {', '.join(str(x) for x in self.page_groups[idx])}  %%\n" if self.range_input.text().replace('%', '').strip() else ""

            nav = f"\n---{range_info}\n{prev_link}{header_link}{next_link}\n\n---\n"

            # tags = [f"#{word[1]}" for word in keywords if re.match(f'.*\\b{word[0]}\\b.*', content, re.IGNORECASE | re.UNICODE | re.MULTILINE | re.DOTALL | re.VERBOSE)]
            tags = [f"#{word[1]}" for word in keywords if word[0].lower() in content.lower()]
            # tags = [f"#{word[1]}" for word in keywords if word[0] in content]
            tag_block = "\n".join(" ".join(tags[i:i + tag_string_len]) for i in range(0, len(tags), tag_string_len))

            full_text = f"\n{nav}\n{tag_block}\n\n---\n{content}"

            with open(os.path.join(base_path, filename), "w", encoding="utf-8") as f:
                f.write(full_text)

        QMessageBox.information(self, "Готово", f"{len(merged_blocks)} файлов сохранено в: {base_path}")
        QMessageBox.warning(self, "Важно", "Часть файлов может не отображаться из проблем с обновлением структуры в Obsidian"
                            "\n\nЛучше закрыть/открыть Obsidian проект заново")

    def handle_mhtml(self):
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть MHTML", "", "MHTML файлы (*.mhtml *.mht)"
        )
        if not self.file_path:
            return

        try:
            with open(self.file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)

            html_content = None

            # Ищем HTML-часть
            if msg.is_multipart():
                parts = msg.iter_parts()
            else:
                parts = [msg]

            for part in parts:
                if part.get_content_type() == "text/html":
                    # Считываем raw payload без декодирования
                    raw = part.get_payload(decode=False)
                    transfer_encoding = (part.get('Content-Transfer-Encoding') or '').lower()
                    charset = part.get_content_charset()

                    # Декодируем quoted-printable, если нужно
                    if transfer_encoding == 'quoted-printable':
                        raw_bytes = quopri.decodestring(raw)
                    else:
                        # decode=True автоматически обработает base64, 7bit, etc.
                        raw_bytes = part.get_payload(decode=True)

                    # Пытаемся определить кодировку
                    encoding_candidates = []
                    if charset:
                        encoding_candidates.append(charset)
                    encoding_candidates += ['utf-8', 'windows-1251']

                    for encoding in encoding_candidates:
                        try:
                            html_content = raw_bytes.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # В крайнем случае — автоопределение
                        detection = chardet.detect(raw_bytes)
                        html_content = raw_bytes.decode(detection['encoding'] or 'utf-8', errors='replace')

                    break

            if not html_content:
                raise ValueError("HTML содержимое не найдено в .mhtml файле.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка чтения MHTML", str(e))
            return

        self.save_as_markdown(html_content)

    def save_as_markdown(self, html_content: str):

        markdown_text = html2text.html2text(html_content)

        ########### fix start
        mark = r"(?:КопироватьРедактировать|Всегда\s+показывать\s+подробности.+?Копировать)"

        pattern = r'(^\s+$)\s+$(\s+' + mark + ')'
        v_pattern = re.compile(pattern, re.MULTILINE | re.DOTALL | re.VERBOSE)
        markdown_text = v_pattern.sub(lambda m: f"{m.group(1)}text\n{m.group(2)}", markdown_text)

        pattern = r'(^\s+\w+$\s+$\s+' + mark + ')'
        v_pattern = re.compile(pattern, re.MULTILINE | re.DOTALL | re.VERBOSE)
        markdown_text = v_pattern.sub(lambda m: f"\n{m.group(1)}", markdown_text)

        pattern = r'^\s+(\w+)$\s+$\s+' + mark + '(.+?^$)'
        v_pattern = re.compile(pattern, re.MULTILINE | re.DOTALL | re.VERBOSE)
        markdown_text = v_pattern.sub(lambda m: f"\n```{m.group(1)}{m.group(2)}```\n", markdown_text)

        pattern = r'(^\s*\*+[^*]+?)\n(\s*```)'
        v_pattern = re.compile(pattern, re.MULTILINE | re.VERBOSE)
        markdown_text = v_pattern.sub(lambda m: f"{m.group(1)}\n'\n{m.group(2)}", markdown_text)

        markdown_text = self.fix_text_replace(markdown_text)

        markdown_text = self.my_massage_format(markdown_text)
        markdown_text = self.table_restore(markdown_text)

        markdown_text = self.fix_text_regexp(markdown_text)

        markdown_text = self.fix_code_blocks(markdown_text)
        ############ fix finish

        self.md_text = markdown_text
        QMessageBox.information(self, "Готово", f"Преобразование завершено:\n{self.file_path}")
        self.mhtml_path_label.setText(self.file_path)
        self.split_pages_cb.setChecked(False)
        self.activate_all_widgets(self, True)

    @staticmethod
    def my_massage_format(text: str) -> str:

        text = re.sub(r'##### Вы сказали:\n(.*?)\n\s*###### ChatGPT сказал:',
                      r"""> [!important] Запрос:
    > \1
    """, text, flags=re.DOTALL)

        return text

    @staticmethod
    def table_restore(text):
        pattern = re.compile(
            r"^((---\|)+---\s*$)(.+?)(^\s{2}$)",
            re.MULTILINE | re.DOTALL
        )

        def process_table_block(match):
            start = match.group(1)  # строка с ---|---|---
            body = match.group(3)  # тело таблицы
            end = match.group(4)  # конец таблицы

            # Разобьем тело на строки
            lines = body.splitlines()

            processed_lines = []
            buffer_line = ""

            for line in lines:

                # Если строка не заканчивается на "  " — это обрыв строки
                if not line.endswith("  "):
                    buffer_line += line + " "
                else:
                    buffer_line += line
                    if buffer_line:
                        processed_lines.append(buffer_line)
                    buffer_line = ""

            # Склеим обратно через \n с сохранением start и end
            return start + "\n" + "\n".join(processed_lines) + "\n" + end

        return pattern.sub(process_table_block, text)

    def fix_text_replace(self, text):
        raw_value = self.config.get("Hard_replacements", "replacements", fallback="")
        replacements = [line.strip() for line in raw_value.strip().splitlines() if line.strip()]
        for replacement in replacements:
            r = replacement.split(':')
            text = text.replace(r[0], r[1])
        return text

    @staticmethod
    def fix_text_regexp(text):
        text = re.sub(r'^.*?(?=>\s*\[!important\]\s*Запрос:)', '\n', text, flags=re.DOTALL)
        text = re.sub(r'^\|', '-|', text, flags=re.MULTILINE)
        return text

    @staticmethod
    def fix_code_blocks(text):
        def replacer(match):
            # Вырезаем содержимое блока и обрабатываем
            code = match.group(2)
            # print(code)
            count = 4
            code = '\n'.join(line[count:] if line.startswith(' ' * count) else line for line in code.splitlines())
            if code.startswith('\n'):
                code = code[1:]
            return f'```{match.group(1)}{code}\n```'

        pattern = r'```(\w+)(.*?)```'
        return re.sub(pattern, replacer, text, flags=re.DOTALL)

    @staticmethod
    def convert_tags(tags : list[str]) -> list[tuple[str, str]]:
        return [(re.sub('_', ' ', re.sub('.·', '/', re.sub(r'^.+/', '', w.strip()))),
                     re.sub(r'.·', '·', w.strip())) for w in tags]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebToMarkdownApp()
    # window.resize(600, 250)
    window.setFixedSize(1000, 500)
    window.show()
    sys.exit(app.exec())
