import openai
import subprocess
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

class App:
    def __init__(self, root):
        self.root = root
        self.when_gpt_4 = 3
        self.iteration = 1

        self.frame = tk.Frame(self.root)
        self.frame.pack()

        self.api_button = tk.Button(self.frame, text="Enter API Key", command=self.get_api_key)
        self.api_button.pack(side="left")

        self.file_button = tk.Button(self.frame, text="Open file", command=self.open_file)
        self.file_button.pack(side="left")

        self.run_button = tk.Button(self.frame, text="Run Code", command=self.run_code)
        self.run_button.pack(side="left")

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
        with open(self.file_path, 'r') as f:
            self.content = f.read()

    def get_user_input(self):
        self.user_input = simpledialog.askstring("Input", "Enter user instructions:")
    
    def run_code(self):
        self.get_user_input()
        self.request_correction(self.content, self.user_input, "", "", "", 1)

    def request_correction(self, content, user_input, previous_code, stdout, stderr, iteration):
        model = "gpt-4"

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
            
        msg_goal = "GOAL: Write ERROR-FREE Python code as per USER INSTRUCTIONS!"
        msg_error_handle = "On ERROR: Use PRINT for error identification & RESOLUTION!"
        msg_code_format = "Code RETURNED in MARKDOWN block. EXPLANATIONS as COMMENTS or DOCSTRINGS. NO REGULAR TEXT!"
        msg_strategy = "USE # or ''' ''' for STRATEGY and THOUGHTS!"

        sys_msg = "GENERATE Python CODE as per USER INSTRUCTIONS. FOCUS on ERROR-FREE code. USE print statements to DEBUG. NO REGULAR TEXT in output. ONLY CODE!"

        if iteration == 1:
            user_msg = f"{msg_goal}\n{msg_error_handle}\n{msg_code_format}\n{msg_strategy}\n\ncontent: {content}\n\nUser instructions:\n{user_input}"
        else:
            user_msg = f"{msg_goal}\n{msg_error_handle}\n{msg_code_format}\n{msg_strategy}\n\nProvided code content:\n{content}\n\nUser instructions:\n{user_input}\n\nPrevious code:\n{previous_code}\n\nStdout:\n{stdout}\n\nStderr:\n{stderr}"

        response = openai.ChatCompletion.create(model=model, messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}])

        response = re.sub(r"```python", "", response.choices[0].message['content'])
        response = re.sub(r"```", "", response)

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
                additional_input = simpledialog.askstring("Input", "Please provide additional instructions to fix the error:")
                user_input += additional_input
                self.request_correction(content, user_input, response, result.stdout, result.stderr, iteration+1)
            else:
                is_correct = messagebox.askyesno("Verify", "The program executed successfully. Is the code running as intended?")
                if not is_correct:
                    additional_input = simpledialog.askstring("Input", "Please provide additional instructions:")
                    user_input += additional_input
                    self.request_correction(content, user_input, response, result.stdout, result.stderr, iteration+1)

root = tk.Tk()
app = App(root)
root.mainloop()

#this script writes scripts of arbitrary length and complexity, the longer the script though, the longer it takes, ditto with complexity. needs more gui elements added.
