# pip install PySide6 html2text requests chardet


"""
Web to Markdown Converter using PySide6

1. save ChatGPT conversations as MHTML
2. convert MHTML to Markdown by this app

"""
import re
import sys

import quopri
import chardet
import requests
import html2text
from email import policy
from email.parser import BytesParser
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QLabel
)


class WebToMarkdownApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web/MHTML → Markdown")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Введите URL веб-страницы")

        self.load_url_button = QPushButton("Загрузить по URL")
        self.load_file_button = QPushButton("Открыть MHTML файл")

        self.layout = QVBoxLayout()
        # self.layout.addWidget(QLabel("Источник URL:"))
        # self.layout.addWidget(self.url_input)
        # self.layout.addWidget(self.load_url_button)
        # self.layout.addWidget(QLabel("Источник .mhtml:"))
        self.layout.addWidget(self.load_file_button)

        self.setLayout(self.layout)

        self.load_url_button.clicked.connect(self.handle_url)
        self.load_file_button.clicked.connect(self.handle_mhtml)

    def handle_url(self):
        url = self.url_input.text().strip()
        if not url.startswith("http"):
            QMessageBox.warning(self, "Ошибка", "Введите корректный URL.")
            return

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except requests.RequestException as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))
            return

        self.save_as_markdown(html_content)

    def handle_mhtml(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть MHTML", "", "MHTML файлы (*.mhtml *.mht)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'rb') as f:
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

        pattern = re.compile(r'^\s*(\w+)$\s+$\s+КопироватьРедактировать(.+?^$)',
            re.MULTILINE | re.DOTALL | re.VERBOSE)

        # Функция замены
        def replacer(match):
            return f"```{match.group(1)}{match.group(2)}```"

        # Заменяем
        markdown_text = pattern.sub(replacer, markdown_text)

        markdown_text = markdown_text.replace('<module>', '<_module_>')

        markdown_text = self.my_massage_format(markdown_text)
        markdown_text = self.table_restore(markdown_text)

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как...", "page", "Markdown Files (*.md)"
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            QMessageBox.information(self, "Успех", f"Сохранено:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))

    @staticmethod
    def my_massage_format(text: str) -> str:

        text = re.sub(r'##### Вы сказали:\n(.*?)\n\s*###### ChatGPT сказал:',
                      r"""> [!important] Вопрос:
    > \1
    """, text, flags=re.DOTALL)

        # for k, v in html_escaping.items():
        #     text = text.replace(k, v)

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
            end = match.group(4)  # строка с * * *

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebToMarkdownApp()
    window.resize(500, 50)
    window.show()
    sys.exit(app.exec())
