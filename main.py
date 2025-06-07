# pip install PySide6 html2text requests chardet

"""
pip install PyInstaller
pip install --upgrade PyInstaller pyinstaller-hooks-contrib

pyinstaller --windowed --onefile --name "ChatGPT to Obsidian" main.py --icon=ChatGPT_Obsidian.ico
"""
import base64

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

# from pprint import pprint

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QLabel, QCheckBox, QGroupBox, QHBoxLayout
)


CONFIG_PATH = "config.ini"

ICON_BASE64 = b"""
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U/7fIhLCP8xRcfrH/VwoUI8jgQuFrEVwOx6IzQYU+T96rBgxhoGuO8SxALsF5DCBXEG5y4SUUtXYiI1osWmgakg5eXOJEJJxq2iogaPUyUA6e6uIWQkenU1gXBT2lMCAjqcBfg6ipPdDNNtGAlOHBEgJLzMAZ/gH//+KAhA6NsOcnW8kFvwNB3xoFwCxkwALOLZFINEA/KcUABmoaxjU8/M/vgRWu3kXzDSVIBRArP9/TwGAMD6AR/IP9P3BWZUgDGB4DJRjG+A/o4DwI2d+Pji1JEjbbQEVzgJZ3KMAjAoIMG5klwSNBMYj1cDT4PSr9UQQFIC/AlL8Mv4BqfcMTFTAn+p46yxQrpoEICogQHMxrASwQ7jPAO3ljwLgN0GqxfPPzwdppN320FfcDGdDYQvY74GUv87+AdklA+koETQf9sUQ2AHQ8x/DQODDhvwW8ehSALxfIT/vAIkKCHTcxH+LWO8cIo+L7io8EtI6B/hrkYjFL3/+vHjMoSJtARb7r4H5/5UHzoR6rMa3X9+rEWOC9A9W//D6j3HgmZY/IF/ImkBXAjb92AEUTWDZyT+dDHzREnjNnfxHE+A8ZHIhEkCPmLIATAC/zQZQTAafkX4kA8Ye0vS6FWBbwAcagL8fSjxH549fEzh3BvQWgFtBkpd/CEoJr/TLRbY/3clAimYQjoD9W5BKPJX58/cMpKYAdvkvagByrhIK/5Sp8D3inck+mkFWAyDawBSIUE/Q83+mqNkWkF/xHzUw8aYK/K0tXwJ6VJSmRhZwxiv4/1eBTb+Be36hNw1cRgBYAI4A/8OQUmHXP71nXMrn+z/YnyvDziCdAH5vZRTA5eEP4Tb9Dah/PsgkQYMwbfCanxsAkX8TMhEDUEj3nxdJbQN604C2gLzhPwaAfwRICP/sWheI/P+LkP2mgfR19RX5/8eAmmC9W8f1/w8CRcH3V8z//2kbSJLIf0RERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERMQi8H/HFrGRPg+Q+QAAAABJRU5ErkJggg==
"""


def load_icon_from_base64():
    icon_data = base64.b64decode(ICON_BASE64)
    pixmap = QPixmap()
    pixmap.loadFromData(icon_data)
    return QIcon(pixmap)


def load_config():
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        config.write(f)


class GPTToMarkdownApp(QWidget):
    def __init__(self):
        super().__init__()

        self.md_text = ""
        self.file_path = ""
        self.now = None
        self.page_groups = []

        self.setWindowTitle("ChatGPT MHTML → Obsidian Markdown")
        self.setWindowIcon(load_icon_from_base64())

        self.config = load_config()

        self.load_file_button = QPushButton("Открыть MHTML файл")
        self.mhtml_path_label = QLabel("")

        self.split_pages_cb = QCheckBox("Разбить по страницам")
        # self.start_page_number_label = QLabel("установить номер первой страницы:")
        self.start_page_number_input = QLineEdit()
        self.page_name_template = QLineEdit("page")
        self.range_input = QLineEdit()
        self.path_label = QLabel("Путь не выбран")
        self.choose_btn = QPushButton("Указать папку сохранения")
        self.save_btn = QPushButton("Сохранить")


        page_row = QHBoxLayout()
        page_row.addWidget(self.split_pages_cb, 1)
        page_row.addWidget(QLabel(), 1)
        page_row.addWidget(QLabel("Стартовый номер для именования страниц. Установите или оставьте пустым. По умолчаюнию = 1:"), 1)
        page_row.addWidget(self.start_page_number_input, 1)
        page_row.addWidget(QLabel(), 3)
        # layout.addLayout(page_row)

        # === Группа "Параметры экспорта"
        group_box_export = QGroupBox("Параметры экспорта")
        group_layout_export = QVBoxLayout(group_box_export)

        # === Группа "Параметры экспорта"
        group_box_pages = QGroupBox("Укажите номера страниц (реальные), которые нужно сохранить")
        group_layout_pages = QVBoxLayout(group_box_pages)

        group_layout_pages.addWidget(QLabel("Оставьте поле ниже пустым для формирования всех страниц"))
        group_layout_pages.addWidget(QLabel("Пример диапазонов (группировка и пересечения возможны):    (1,4),5,(8,11-13),15-18,6-9"))
        group_layout_pages.addWidget(self.range_input)

        group_layout_export.addLayout(page_row)
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
        default_save_path = self.config.get("Settings", "default_save_path", fallback=".")
        default_load_path = self.config.get("Settings", "default_load_path", fallback=".")
        self.export_path = default_save_path
        self.load_path = default_load_path
        self.path_label.setText("Путь к проекту Obsidian: "+default_save_path)

        self.activate_all_widgets(self, False)

    def on_checkbox_toggled(self, checked: bool):
        if checked:
            self.range_input.setEnabled(True)
            self.page_name_template.setEnabled(True)
            self.start_page_number_input.setEnabled(True)
        else:
            self.range_input.setEnabled(False)
            self.page_name_template.setEnabled(False)
            self.start_page_number_input.setEnabled(False)
        # print("✅" if checked else "❌")

    def activate_all_widgets(self, parent: QWidget, status: bool = True):
        for widget in parent.findChildren(QWidget, options=Qt.FindChildrenRecursively):
            widget.setEnabled(status)
            self.load_file_button.setEnabled(True)
        if status:
            self.range_input.setEnabled(False)
            self.page_name_template.setEnabled(False)
            self.start_page_number_input.setEnabled(False)
            self.start_page_number_input.clear()
            self.range_input.clear()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Укажите путь к проекту Obsidian", self.export_path)
        if folder:
            self.export_path = folder
            self.path_label.setText("Путь к проекту Obsidian: "+folder)
            self.config.set("Settings", "default_save_path", folder)
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
        # folder_path = f'exported_{self.now}/'
        folder_path = ''
        try:
            spn = int(self.start_page_number_input.text().strip())
        except ValueError:
            spn = 1
            self.start_page_number_input.setText("1")
        # print(spn)
        page = self.page_name_template.text()
        page = 'page' if page.strip()=='' else page
        self.now = datetime.now().strftime("%Y%m%d%H%M%S")
        base_path = self.export_path
        if self.split_pages_cb.isChecked():
            base_path = os.path.join(base_path, f"exported_{self.now}")
            os.makedirs(base_path, exist_ok=True)
            blocks = self.split_text(self.md_text)
            with open(os.path.join(base_path, f"headers_{spn}.md"), "w", encoding="utf-8") as f:
                f.writelines('\n')
                for idx, block in enumerate(blocks):
                    blocks[idx] = "№ "+str(idx+1)+"\n"+block
                    f.writelines(f"[[{folder_path}{page} {idx+spn:03}|{idx+spn}]]     запрос №   {idx + 1}\n{self.get_line(block)}"+"\n"*2)

            merged = self.merge_blocks(blocks)
            if self.range_input.text().strip():
                with open(os.path.join(base_path, f"headers_{spn}.md"), "w", encoding="utf-8") as f:
                    f.writelines('\n')
                    for m_idx, m_block in enumerate(merged):
                        f.writelines(f"%%  Запросы:  {', '.join(str(x) for x in self.page_groups[m_idx])}  %%\n")
                        f.writelines(f"[[{folder_path}{page} {m_idx+spn:03}|{m_idx+spn}]]     запрос №   {m_idx + 1}\n{self.get_line(m_block[0], 3)}"+"\n"*2)
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
        # folder_path = f'exported_{self.now}/'
        folder_path = ''
        try:
            spn = int(self.start_page_number_input.text().strip())
        except ValueError:
            spn = 1
            self.start_page_number_input.setText("1")
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
            # print(content)
            # print('='*100)
            filename = f"{page} {idx+spn:03}.md"
            prev_link = f"[[{folder_path}{page} {idx-1+spn:03}|{page} {idx-1+spn:03}]]  <"+" "*10 if idx > 0 else ""
            header_link = f"[[{folder_path}headers_{spn}|headers_{spn}]]"+" "*10
            next_link = f">  [[{folder_path}{page} {idx+1+spn:03}|{page} {idx+1+spn:03}]]" if idx < len(merged_blocks) - 1 else ""
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
            self, "Открыть MHTML", self.load_path, "MHTML файлы (*.mhtml *.mht)"
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
    icon = load_icon_from_base64()
    app.setWindowIcon(icon)  # ✅ ВАЖНО: для панели задач
    window = GPTToMarkdownApp()
    # window.resize(600, 250)
    window.setFixedSize(1000, 500)
    window.show()
    sys.exit(app.exec())
