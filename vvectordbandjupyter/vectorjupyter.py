from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QVBoxLayout, QTextEdit, QLabel, QLineEdit, QPushButton, QInputDialog)
import re
import sys
from jupyter_client.manager import start_new_kernel
import openai
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection,
    utility
)
import os

def get_openai_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']

def store_embedding(collection, text, model):
    embedding = get_openai_embedding(text, model)
    vectors = [[text, embedding]]
    mr = collection.insert(vectors)
    return mr

def initialize_embedding_model(model="text-embedding-ada-002"):
    return model

def initialize_milvus():
    connections.connect(host="localhost", port="19530", alias="default")
    collection_name = "OpenAI_Embeddings"
    fields = [
        FieldSchema(name="name", dtype=DataType.VARCHAR, is_primary=True, description="name of the embedding", ),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024, description="the embedding vector")
    ]
    schema = CollectionSchema(fields=fields, param("max_length": 256), description="Collection of OpenAI Embeddings")
    
    if collection_name not in utility.list_collections():
        collection = Collection(name=collection_name, schema=schema)
    
    return connections.get_connection(alias="default"), collection_name


def store_embedding(collection, text, model):
    embedding = get_openai_embedding(text, model)
    vectors = [{"name": text, "embedding": embedding}]
    collection.insert([vectors])
    collection.flush()

class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()

        self.file_exists = False
        self.iteration = 1
        self.content = ""
        self.user_input = ""
        self.kernel_manager, self.kernel_client = start_new_kernel(kernel_name="python3")

        # Initialize Milvus and OpenAI components
        self.embedding_model = initialize_embedding_model()
        self.milvus_client, self.collection_name = initialize_milvus()

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

    def get_api_key(self):
        api_key, okPressed = QInputDialog.getText(self, "Input", "Please enter your OpenAI API Key:")
        if okPressed:
            openai.api_key = api_key

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
                                                  options=options)
        if fileName:
            with open(fileName, 'r') as f:
                self.content = f.read()
                self.file_exists = True

    def get_user_input(self):
        user_input, okPressed = QInputDialog.getText(self, "Input", "Enter user instructions:")
        if okPressed:
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
        
    if not os.path.isfile('workspace.txt'):
        with open('workspace.txt', 'w'): pass

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

        if iteration == 1:
            store_embedding(self.milvus_client, self.collection_name, self.embedding_model, user_input)
            store_embedding(self.milvus_client, self.collection_name, self.embedding_model, content)
        else:
            store_embedding(self.milvus_client, self.collection_name, self.embedding_model, previous_code)
            store_embedding(self.milvus_client, self.collection_name, self.embedding_model, stdout)

        embedding = get_openai_embedding(self.embedding_model, user_input)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        topk = 10
        _, results = self.milvus_client.search(self.collection_name, topk, query_embedding=[embedding], params=search_params)
        context = []
        for result in results[0]:
            _, entities = self.milvus_client.get_entity_by_id(self.collection_name, [result.id])
            context.append(entities[0].embedding)

        context_text = [self.embedding_to_text[e.tobytes()] for e in context]

        for text in context_text:
            messages.append({"role": "assistant", "content": text})

        response = openai.ChatCompletion.create(model=model, messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}])

        response = re.sub(r"", "", response.choices[0].message['content'])
        response = re.sub(r"", "", response)

        self.update_code_view(response)

        with open('response.py', 'w') as f:
            f.write(response)

        try:
            result = subprocess.run(['python', 'response.py'], capture_output=True, text=True)
        except FileNotFoundError:
            print("File not found error!")
        except Exception as general_exception:
            print("An error occurred: ", general_exception)
        else:
            if result.returncode != 0:
                additional_input, okPressed = QInputDialog.getText(self, "Input", "Please provide additional instructions to fix the error:")
                if okPressed:
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
                    additional_input, okPressed = QInputDialog.getText(self, "Input", "Please provide additional instructions:")
                    if okPressed:
                        user_input += additional_input
                        self.request_correction(content, user_input, response, result.stdout, result.stderr, iteration+1)

    def run_jupyter_kernel_code(self, code):
        self.kernel_client.execute(code)

        stdout = ''
        traceback = None

        while True:
            try:
                msg = self.kernel_client.get_iopub_msg(timeout=1)["content"]
            except KeyError:
                continue
            except KeyboardInterrupt:
                self.kernel_manager.shutdown_kernel()
                break

            if 'name' in msg:
                if msg['name'] == 'stdout':
                    stdout += msg['text']

                if msg['name'] == 'traceback':
                    traceback = msg['traceback']

            if 'execution_state' in msg and msg['execution_state'] == 'idle':
                break

        return {"stdout": stdout, "traceback": traceback}

# after class definition...
app = QtWidgets.QApplication(sys.argv)
window = Ui()
sys.exit(app.exec_())
