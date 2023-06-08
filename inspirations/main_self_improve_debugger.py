import openai
import os
import subprocess

# Make sure to replace <your_api_key> with your actual API key
# openai.api_key = "<your_api_key>"

def ask_gpt3(question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful python coding AI who will generate code and provide suggestions for Python projects based on the user's input or generate ideas and code if the user doesn't provide an idea. start the code block with 'python' word. only write in code block. use comments to explain yourself if needed. "},
            {"role": "user", "content": question}
        ]
    )
   
    try:
        generated_text = response["choices"][0]["message"]["content"]
        print("GENERATED TEXT: " + generated_text)
        #strip all character after the last triple backtick
        generated_text = generated_text[:generated_text.rfind('```')]
        print("GENERATED TEXT: " + generated_text)
        
        
        # return everything after the first occurrence of the word 'python'
        return generated_text.split('python', 1)[1]
    except IndexError:
        # try the call again up to 3 times. if all 3 fail, return the error message
        for i in range(2):
            response = ask_gpt3(question)
            try:
                return generated_text.split('python', 1)[1]
            except IndexError:
                print("Error: GPT-3 failed to generate code. Please try again.")
                pass

        
    

def get_project_idea(user_input):
    if user_input == "":
        return "Generate a Python project idea and provide sample code . Write the code in one code block between triple backticks."
    else:
        return f"Generate code for the Python project '{user_input}' . Write the code in one code block between triple backticks. comment the code."

def create_experiments_folder():
    if not os.path.exists("experiments"):
        os.mkdir("experiments")

def save_generated_code(code, filename=None):
    create_experiments_folder()
    if filename is None:
        file_number = 1
        while os.path.exists(f"experiments/ex_{file_number}.py"):
            file_number += 1
        filename = f"experiments/ex_{file_number}.py"
    else:
        file_number = None

    with open(filename, "w") as f:
        f.write(code)
    return file_number

def run_code_file(filename):
    # ask the user to confirm before running the code because it could be malicious
    to_run = input("CAUTION! Check the code in the file before running it. Press Enter to continue.")

    if to_run == "":
        
        result = subprocess.run(
            ["python", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout, result.stderr


def main():
    print("Welcome to the GPT-4 Auto Coder and Self Improver!")
    while True:
        self_improve = False
        user_input = input("\nDo you want to improve an existing file (type 'yes') or continue with the generated file (type 'no')? ").strip().lower()
        if user_input == 'yes':
            self_improve = True
            files = [f for f in os.listdir("files_to_improve") if f.endswith('.py')]
            if not files:
                print("No files found in the 'experiments' folder.")
            else:
                print("\nList of files in the 'files_to_improve' folder:")
                for index, file in enumerate(files):
                    print(f"{index + 1}. {file}")
                selected_file = int(input("\nChoose a file number to improve: ")) - 1
                with open(f"files_to_improve/{files[selected_file]}", "r") as f:
                    # read line by line and add the linebreaks
                    response = ""
                    for line in f:
                        response += line
                    # print(response)
                    #print the first 1000 characters of the file
                    print("The first 100 characters of the file are: " + response[:100])
                filename_prefix = files[selected_file].rsplit(".", 1)[0]

        elif user_input == 'no':
            user_input = input("\nPlease enter an idea for a Python project or leave it blank for a random suggestion (type 'quit' to exit): ").strip()
        if user_input.lower() == "quit":
            break
        # else:
        #     filename_prefix = f"ex_{file_number}"
        
        
        
        if not self_improve:
            gpt3_question = get_project_idea(user_input)
            response = ask_gpt3(gpt3_question)
            file_number = save_generated_code(response)
            print(f"\nAssistant: The generated code has been saved as 'experiments/ex_{file_number}.py'.")
        elif self_improve:
            num_attempts = int(input("\nHow many iterations of improvement would you like? (Enter 0 for no improvements): "))
            for attempt in range(1, num_attempts + 1):
                gpt3_question = f"Code to be improved is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. write the improved code in one code block. Commment about the changes you are making. "
                # print("gpt_question: " + gpt3_question)
                print("Improving code...")
                response = ask_gpt3(gpt3_question)
                update_filename = f"experiments/{filename_prefix}_update_{attempt}.py"
                save_generated_code(response, filename=update_filename)
                print(f"\nAssistant: The improved code has been saved as '{update_filename}'.")
                # check if all iterations are done then break
                if attempt == num_attempts:
                    break

       
        


        num_attempts = int(input("\nHow many iterations of improvement would you like? (Enter 0 for no improvements): "))
        for attempt in range(1, num_attempts + 1):
             # run the code and receive the output and error message
            output, error_message = run_code_file(f"experiments/ex_{file_number}.py")
            # print(f"\nOutput:\n{output[]}")
            if error_message:
                print(f"\nError Message:\n{error_message[-100:]}")
                gpt3_question = f"The current code is:\n```\n{response}\n```\nError message:\n```\n{error_message[-100:]}\n```\nImprove the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Commment about the changes you are making."
                print("QUESTION: " + gpt3_question)
            else:
                gpt3_question = f"The current code is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Commment about the changes you are making. "
            print("Improving code...")
            response = ask_gpt3(gpt3_question)
            update_filename = f"experiments/ex_{file_number}_update_{attempt}.py"
            save_generated_code(response, filename=update_filename)
            print(f"\nAssistant: The improved code has been saved as '{update_filename}'.")
if __name__ == "__main__":
    main()


