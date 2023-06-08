from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QVBoxLayout, QTextEdit, QLabel, QPushButton, QInputDialog, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal
import openai
import re
import sys
import os
import subprocess


class Worker(QThread):
    progress = pyqtSignal(int)
    new_log_message = pyqtSignal(str)  # New Signal
    finished = pyqtSignal(str, str, str, str, str, int)

    def __init__(self, ui, content, user_input, previous_code, stdout, stderr, iteration):
        super().__init__()
        self.ui = ui
        self.content = content
        self.user_input = user_input
        self.previous_code = previous_code
        self.stdout = stdout
        self.stderr = stderr
        self.iteration = iteration

    def log(self, message):
        self.new_log_message.emit(message)
        self.progress.emit(10)
        model = "gpt-4"

        if self.iteration == 1:
            message_content = f"""
            content: {self.content}
            User instructions:
            {self.user_input}
            """
        else:
            message_content = f"""
            code content: {self.content}
            User instructions:
            {self.user_input}
            Previous code:
            {self.previous_code}
            Stdout:
            {self.stdout}
            Stderr:
            {self.stderr}
            """

        sys_msg = "GENERATE Python CODE as per USER INSTRUCTIONS. FOCUS on ERROR-FREE code. USE print statements to DEBUG. NO REGULAR TEXT in output. ONLY CODE! openai's API documentation has been updated. DO NOT edit the model or syntax!"
        self.progress.emit(20)

        if self.iteration == 1:
            user_msg = f"content: {self.content}\n\nUser instructions:\n{self.user_input}"
        else:
            user_msg = f"Provided code content:\n{self.content}\n\nUser instructions:\n{self.user_input}\n\nPrevious code:\n{self.previous_code}\n\nStdout:\n{self.stdout}\n\nStderr:\n{self.stderr}"
        self.progress.emit(30)

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ]

        self.log("Requesting code from OpenAI...")
        response = openai.ChatCompletion.create(model=model, messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}])
        self.progress.emit(50)
        self.log("Received code from OpenAI...")

        response = re.sub(r"", "", response.choices[0].text.strip())
        response = re.sub(r"", "", response)
        self.log("Processed OpenAI response...")

        with open('response.py', 'w') as f:
            f.write(response)
        self.log("Written response to response.py...")
        self.progress.emit(60)

        result = subprocess.run(['python', 'response.py'], capture_output=True, text=True)
        self.log("Executed response.py...")
        self.progress.emit(80)

        self.finished.emit(self.content, self.user_input, response, result.stdout, result.stderr, self.iteration+1)
        self.log("Worker thread completed...")
        self.progress.emit(100)


class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()

        self.file_exists = False
        self.iteration = 1
        self.content = ""
        self.user_input = ""

        layout = QVBoxLayout()

        self.api_key_button = QPushButton('Enter API Key')
        self.api_key_button.clicked.connect(self.get_api_key)
        layout.addWidget(self.api_key_button)

        self.open_file_button = QPushButton('Open File')
        self.open_file_button.clicked.connect(self.open_file)
        layout.addWidget(self.open_file_button)

        self.run_no_file_button = QPushButton('Run Without File')
        self.run_no_file_button.clicked.connect(self.run_code_without_file)
        layout.addWidget(self.run_no_file_button)

        self.run_with_file_button = QPushButton('Run With File')
        self.run_with_file_button.clicked.connect(self.run_code_with_file)
        layout.addWidget(self.run_with_file_button)

        self.code_view = QTextEdit()
        layout.addWidget(QLabel('Code View'))
        layout.addWidget(self.code_view)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle('My App')
        self.show()

        if not os.path.isfile('workspace.txt'):
            with open('workspace.txt', 'w'): pass

    def get_api_key(self):
        api_key, _ = QInputDialog.getText(self, "Input", "Please enter your OpenAI API Key:")
        openai.api_key = api_key

    def open_file(self):
        self.log("Opening file...")
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
                                                  options=options)
        if fileName:
            with open(fileName, 'r') as f:
                self.content = f.read()
                self.file_exists = True
                self.log("File opened successfully.")

    def get_user_input(self):
        user_input, _ = QInputDialog.getText(self, "Input", "Enter user instructions:")
        self.user_input = user_input

    def run_code_without_file(self):
        self.get_user_input()
        self.file_exists = False
        self.run_code()

    def run_code_with_file(self):
        if not self.file_exists:
            QMessageBox.information(self, "Information", "Please open a file first.")
        else:
            self.get_user_input()
            self.run_code()

    def update_code_view(self, code):
        self.code_view.clear()
        self.code_view.insertPlainText(code)

    def run_code(self):
        self.log("Initiating code generation...")
        self.worker = Worker(self, self.content, self.user_input, "", "", "", 1)
        self.worker.finished.connect(self.request_correction_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.new_log_message.connect(self.log)  # Connecting the signal to the log slot
        self.worker.start()

    def request_correction_finished(self, content, user_input, previous_code, stdout, stderr, iteration):
        self.log("Requesting error correction...")
        additional_input, _ = QInputDialog.getText(self, "Input", "Please provide additional instructions to fix the error:")
        user_input += additional_input
        self.content = content
        self.user_input = user_input

        self.worker = Worker(self, content, self.user_input, previous_code, stdout, stderr, iteration)
        self.worker.finished.connect(self.request_correction_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.start()
        
    def log(self, message):
        self.code_view.append(f"{message}\n")
        self.code_view.repaint()

    def update_progress(self, value):
        self.progress_bar.setValue(value)


app = QtWidgets.QApplication(sys.argv)
window = Ui()
sys.exit(app.exec_())

