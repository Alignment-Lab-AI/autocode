from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QVBoxLayout, QTextEdit, QLabel, QLineEdit, QPushButton, QInputDialog)
import openai
import re
import sys
from jupyter_client.manager import start_new_kernel
import os

class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()

        self.file_exists = False
        self.iteration = 1
        self.content = ""
        self.user_input = ""
        self.kernel_manager, self.kernel_client = start_new_kernel(kernel_name="python3")

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

        self.setLayout(layout)
        self.setWindowTitle('My App')
        self.show()

        if not os.path.isfile('workspace.txt'):
            with open('workspace.txt', 'w'): pass

    def get_api_key(self):
        api_key, _ = QInputDialog.getText(self, "Input", "Please enter your OpenAI API Key:")
        openai.api_key = api_key

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
                                                  options=options)
        if fileName:
            with open(fileName, 'r') as f:
                self.content = f.read()
                self.file_exists = True

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
        self.request_correction(self.content, self.user_input, "", "", "", 1)

    def request_correction(self, content, user_input, previous_code, stdout, stderr, iteration):
        model = "gpt-4"

        if not self.file_exists:
            content = ""

        if iteration == 1:
            message_content = f"""
            content: {content}
            User instructions:
            {user_input}
            """
        else:
            message_content = f"""
            code content: {content}
            User instructions:
            {user_input}
            Previous code:
            {previous_code}
            Stdout:
            {stdout}
            Stderr:
            {stderr}
            """

        sys_msg = "GENERATE Python CODE as per USER INSTRUCTIONS. FOCUS on ERROR-FREE code. USE print statements to DEBUG. NO REGULAR TEXT in output. ONLY CODE!"

        if iteration == 1:
            user_msg = f"content: {content}\n\nUser instructions:\n{user_input}"
        else:
            user_msg = f"Provided code content:\n{content}\n\nUser instructions:\n{user_input}\n\nPrevious code:\n{previous_code}\n\nStdout:\n{stdout}\n\nStderr:\n{stderr}"

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ]

        response = openai.ChatCompletion.create(model=model, messages=messages)

        response = re.sub(r"", "", response.choices[0].message['content'])
        response = re.sub(r"", "", response)

        self.update_code_view(response)

        with open('workspace.txt', 'a') as f:
            f.write(response + "\n")

        response = openai.ChatCompletion.create(model=model, messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}])

        response = re.sub(r"", "", response.choices[0].message['content'])
        response = re.sub(r"", "", response)

        self.update_code_view(response)

        with open('response.py', 'w') as f:
            f.write(response)

        result = subprocess.run(['python', 'response.py'], capture_output=True, text=True)

        if result.returncode != 0:
            additional_input, _ = QInputDialog.getText(self, "Input", "Please provide additional instructions to fix the error:")
            user_input += additional_input
            self.request_correction(content, user_input, response, result.stdout, result.stderr, iteration+1)

        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("The program executed successfully. Is the code running as intended?")
            msgBox.setWindowTitle("Verify")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            returnValue = msgBox.exec()
            if returnValue == QMessageBox.No:
                additional_input, _ = QInputDialog.getText(self, "Input", "Please provide additional instructions:")
                user_input += additional_input
                self.request_correction(content, user_input, response, result.stdout, result.stderr, iteration+1)

app = QtWidgets.QApplication(sys.argv)
window = Ui()
sys.exit(app.exec_())

