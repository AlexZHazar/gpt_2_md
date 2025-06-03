from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from bs4 import BeautifulSoup
import re
import sys


html_escaping = {
    '&amp;' : '&',
    '&lt;' : '<',
    '&gt;' : '>',
    '&quot;' : '"',
    '&apos;' : "'"
    }

# r_html_escaping = {v: k for k, v in html_escaping.items()}


def my_massage_format(text: str) -> str:

    text = re.sub(r'##### Вы сказали:\n(.*?)\n\s*###### ChatGPT сказал:',
                  r"""> [!important] Вопрос:
> \1
""", text, flags=re.DOTALL)

    for k, v in html_escaping.items():
        text = text.replace(k, v)

    return text


def extract_code_from_html_block(html_block: str) -> str:
    # print(html_block)
    # print('=' * 50)
    soup = BeautifulSoup(html_block, "html.parser")
    code_tag = soup.find("code")
    if not code_tag:
        return ""
    code_id = code_tag.get("id", "")
    language = code_id.replace("code-lang-", "") if code_id.startswith("code-lang-") else ""

    text_only = re.sub(r"</?span[^>]*>", "", html_block)
    text_only = text_only.replace('```\n', '')
    text_only = text_only.replace('</code></p></div>', '')
    text_only = re.sub(r"<div>.+>", "", text_only).replace('&gt;', '>')
    # print(text_only)
    # print('=' * 50)

    return f"```{language}\n{text_only}"


def replace_html_code_blocks(markdown: str) -> str:
    pattern = re.compile(r"```\s*\n\s*<div><p>.*?</p><p><code.*?</code></p></div>\s*\n\s*```", re.DOTALL)

    def replacer(match):
        html_block = match.group(0)
        return extract_code_from_html_block(html_block)

    return pattern.sub(replacer, markdown)

class MarkdownCleaner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown HTML → Markdown Code")
        self.resize(800, 600)

        self.layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        self.btn_open = QPushButton("Открыть Markdown-файл")
        self.btn_open.clicked.connect(self.open_file)
        self.layout.addWidget(self.btn_open)

        self.btn_process = QPushButton("Преобразовать HTML-блоки")
        self.btn_process.clicked.connect(self.process_text)
        self.layout.addWidget(self.btn_process)

        self.btn_save = QPushButton("Сохранить как...")
        self.btn_save.clicked.connect(self.save_file)
        self.layout.addWidget(self.btn_save)

        self.file_path = None

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть Markdown-файл", "", "Markdown (*.md);;Все файлы (*)")
        if path:
            self.file_path = path
            with open(path, 'r', encoding='utf-8') as f:
                self.text_edit.setPlainText(f.read())

    def process_text(self):
        original_text = self.text_edit.toPlainText()
        processed = replace_html_code_blocks(original_text)
        processed_fixed = '\n-------\n\n'+my_massage_format(processed)
        self.text_edit.setPlainText(processed_fixed)
        QMessageBox.information(self, "Готово", "HTML-блоки преобразованы.")

    def save_file(self):
        if not self.text_edit.toPlainText().strip():
            QMessageBox.warning(self, "Ошибка", "Текст пуст.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Markdown (*.md);;Все файлы (*)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "Сохранено", f"Файл сохранён:\n{path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MarkdownCleaner()
    window.show()
    sys.exit(app.exec())
