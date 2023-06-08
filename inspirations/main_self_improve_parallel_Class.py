import openai
import os
import concurrent.futures
import re

class GPT4AutoCoderSelfImprover:

    def __init__(self):
        self.process_inputs_list = []
        

    @staticmethod
    def ask_gpt3(question):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful python coding AI who will generate code and provide suggestions for Python projects based on the user's input or generate ideas and code if the user doesn't provide an idea. start the code block with 'python' word. "},
                {"role": "user", "content": question}
            ]
        )
       
        try:
            generated_text = response["choices"][0]["message"]["content"]
            print("GENERATED TEXT: " + generated_text)
            generated_text = generated_text[:generated_text.rfind('```')]
            return generated_text.split('python', 1)[1]
        except IndexError:
            for i in range(2):
                response = GPT4AutoCoderSelfImprover.ask_gpt3(question)
                try:
                    return generated_text.split('python', 1)[1]
                except IndexError:
                    print("Error: GPT-3 failed to generate code. Please try again.")
                    pass

    @staticmethod
    def get_project_idea(user_input):
        if user_input == "":
            return "Generate a Python project idea and provide sample code . Write the code in one code block between triple backticks. comment the code"
        else:
            return f"Generate code for the Python project '{user_input}' . Write the code in one code block between triple backticks. comment the code."

    @staticmethod
    def create_experiments_folder():
        if not os.path.exists("experiments"):
            os.mkdir("experiments")

    @staticmethod
    def save_generated_code(code, process_folder, filename=None, use_original_filename=False):
        if not os.path.exists(process_folder):
            os.makedirs(process_folder)

        if filename is None:
            file_number = 1
            while os.path.exists(f"{process_folder}/ex_{file_number}.py"):
                file_number += 1
            filename = f"{process_folder}/ex_{file_number}.py"
        elif not use_original_filename:
            file_number_match = re.search(r'ex_(\d+)', filename)
            if file_number_match:
                file_number = int(file_number_match.group(1))
            else:
                raise ValueError("Invalid filename format. Cannot extract file number.")

        with open(filename, "w", encoding="utf-8") as file:
            file.write(code)

        return file_number if not use_original_filename else None


    @staticmethod
    def get_process_inputs(process_number):
        print(f"\nCollecting inputs for process {process_number}...")

        self_improve = False
        selected_file = None
        user_input = None
        self_improve_input = input(f"Do you want to improve an existing file for process {process_number}? (type 'yes' or 'no'): ").strip().lower()

        if self_improve_input == 'yes':
            self_improve = True
            files = [f for f in os.listdir("files_to_improve") if f.endswith('.py')]

            if not files:
                print("No files found in the 'files_to_improve' folder.")
            else:
                print(f"\nList of files in the 'files_to_improve' folder for process {process_number}:")
                for index, file in enumerate(files):
                    print(f"{index + 1}. {file}")

                selected_file = int(input(f"Choose a file number to improve for process {process_number}: ")) - 1
                selected_file = files[selected_file]
        else:
            user_input = input(f"Enter an idea for a Python project for process {process_number} or leave it blank for a random suggestion (type 'quit' to exit): ").strip()

        num_improvements = int(input(f"How many iterations of improvement would you like for process {process_number}? (Enter 0 for no improvements): "))

        return {
            "user_input": user_input,
            "self_improve": self_improve,
            "selected_file": selected_file,
            "num_improvements": num_improvements
        }

    @staticmethod
    def create_process_folder(process_number):
        process_folder = f"experiments/process_{process_number}"
        if not os.path.exists(process_folder):
            os.makedirs(process_folder)
        return process_folder

    @staticmethod
    def run_process(process_number, process_inputs):
        print(f"\nStarting process {process_number}...")
        process_folder = GPT4AutoCoderSelfImprover.create_process_folder(process_number)
        GPT4AutoCoderSelfImprover.main(process_inputs, process_folder)

    @staticmethod
    def main(process_inputs, process_folder):
        print(f"Welcome to the GPT-4 Auto Coder and Self Improver for process {process_folder}!")

        user_input = process_inputs['user_input']
        self_improve = process_inputs['self_improve']
        selected_file = process_inputs['selected_file']
        num_improvements = process_inputs['num_improvements']

        file_number = None  # Initialize file_number variable here

        if not self_improve:
            gpt3_question = GPT4AutoCoderSelfImprover.get_project_idea(user_input)
            response = GPT4AutoCoderSelfImprover.ask_gpt3(gpt3_question)
            file_number = GPT4AutoCoderSelfImprover.save_generated_code(response, process_folder)
            print(f"\nAssistant: The generated code has been saved as '{process_folder}/ex_{file_number}.py'.")
            filename_prefix = f"ex_{file_number}"

            # Add improvement process for non self_improve
            filename_prefix = f"ex_{file_number}"
            for attempt in range(1, num_improvements + 1):
                gpt3_question = f"Code to be improved is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Write the improved code in one code block between triple backticks. Comment about the changes you are making."
                print("Improving code...")
                response = GPT4AutoCoderSelfImprover.ask_gpt3(gpt3_question)
                update_filename = f"{process_folder}/{filename_prefix}_update_{attempt}.py"
                GPT4AutoCoderSelfImprover.save_generated_code(response, process_folder=process_folder, filename=update_filename)
                print(f"\nAssistant: The improved code has been saved as '{update_filename}'.")
        
        else:
            with open(f"files_to_improve/{selected_file}", "r") as f:
                response = f.read()
            print("The first 100 characters of the file are: " + response[:100])
            
            # Use the original filename without the extension as the prefix
            filename_prefix = os.path.splitext(os.path.basename(selected_file))[0]

            

            for attempt in range(1, num_improvements + 1):
                gpt3_question = f"Code to be improved is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Write the improved code in one code block between triple backticks. Comment about the changes you are making."
                print("Improving code...")
                response = GPT4AutoCoderSelfImprover.ask_gpt3(gpt3_question)
                update_filename = f"{process_folder}/{filename_prefix}_update_{attempt}.py"
                GPT4AutoCoderSelfImprover.save_generated_code(response, process_folder=process_folder, filename=update_filename, use_original_filename=self_improve)
                print(f"\nAssistant: The improved code has been saved as '{update_filename}'.")

    @staticmethod
    def main_concurrent():
        print("Welcome to the GPT-4 Auto Coder and Self Improver!")
        while True:
            num_processes = int(input("\nHow many processes do you want to start? (Enter 0 to exit): "))
            if num_processes == 0:
                break

            process_inputs_list = []
            for i in range(1, num_processes + 1):
                process_inputs = GPT4AutoCoderSelfImprover.get_process_inputs(i)
                process_inputs_list.append(process_inputs)

            with concurrent.futures.ProcessPoolExecutor() as executor:
                # Start the specified number of processes in parallel
                process_numbers = range(1, num_processes + 1)
                list(executor.map(GPT4AutoCoderSelfImprover.run_process, process_numbers, process_inputs_list))

            print("All processes completed.")



if __name__ == "__main__":
    Auto_Coder = GPT4AutoCoderSelfImprover()
    Auto_Coder.main_concurrent()

