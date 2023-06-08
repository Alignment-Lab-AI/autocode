import openai
import subprocess
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Text, Scrollbar
import sys
from jupyter_client.manager import start_new_kernel

class App:
    def __init__(self, root):
        self.root = root
        self.when_gpt_4 = 3
        self.iteration = 1
        self.file_exists = False
        self.kernel_manager, self.kernel_client = start_new_kernel(kernel_name="python3")

        self.frame = tk.Frame(self.root)
        self.frame.pack()

        self.api_button = tk.Button(self.frame, text="Enter API Key", command=self.get_api_key)
        self.api_button.pack(side="left")

        self.file_button = tk.Button(self.frame, text="Open file", command=self.open_file)
        self.file_button.pack(side="left")

        self.run_button = tk.Button(self.frame, text="Run Without File", command=self.run_code_without_file)
        self.run_button.pack(side="left")

        self.run_button_with_file = tk.Button(self.frame, text="Run With File", command=self.run_code_with_file)
        self.run_button_with_file.pack(side="left")

        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack()

        self.text_scrollbar = Scrollbar(self.text_frame)
        self.text_scrollbar.pack(side="right", fill="y")

        self.code_view = Text(self.text_frame, wrap="word", yscrollcommand=self.text_scrollbar.set)
        self.code_view.pack(side="left", fill="both")
        self.text_scrollbar.config(command=self.code_view.yview)

        self.content = ''
        self.user_input = ''
        self.previous_code = ''
        self.stdout = ''
        self.stderr = ''

    def get_api_key(self):
        self.api_key = simpledialog.askstring("Input", "Please enter your OpenAI API Key:")
        openai.api_key = self.api_key

    def open_file(self):
        self.file_path = filedialog.askopenfilename()
        self.file_exists = True
        with open(self.file_path, 'r') as f:
            self.content = f.read()

    def get_user_input(self):
        self.user_input = simpledialog.askstring("Input", "Enter user instructions:")

    def run_code_without_file(self):
        self.get_user_input()
        self.file_exists = False
        self.run_code()

    def run_code_with_file(self):
        if not self.file_exists:
            messagebox.showinfo("Information", "Please open a file first.")
        else:
            self.get_user_input()
            self.run_code()

    def run_code(self):
        self.request_correction(self.content, self.user_input, "", "", "", 1)

    def update_code_view(self, code):
        self.code_view.delete(1.0, "end")
        self.code_view.insert("insert", code)

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

        response = openai.ChatCompletion.create(model=model, messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}])

        response = re.sub(r"", "", response.choices[0].message['content'])
        response = re.sub(r"", "", response)

        self.update_code_view(response)

        result = self.run_jupyter_kernel_code(response)

        if result['traceback'] is not None:
            additional_input = simpledialog.askstring("Input", "Please provide additional instructions to fix the error:")
            user_input += additional_input
            self.request_correction(content, user_input, response, result['stdout'], result['traceback'], iteration+1)
        else:
            is_correct = messagebox.askyesno("Verify", "The program executed successfully. Is the code running as intended?")
            if not is_correct:
                additional_input = simpledialog.askstring("Input", "Please provide additional instructions:")
                user_input += additional_input
                self.request_correction(content, user_input, response, result['stdout'], result['traceback'], iteration+1)

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

            if msg['name'] == 'stdout':
                stdout += msg['text']

            if msg['name'] == 'traceback':
                traceback = msg['traceback']

            if msg['execution_state'] == 'idle':
                break

        return {"stdout": stdout, "traceback": traceback}

root = tk.Tk()
app = App(root)
root.mainloop()
