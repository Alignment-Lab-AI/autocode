import gradio as gr
from main_self_improve_Class import GPT4AutoCoder
import os

# get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")
auto_coder = GPT4AutoCoder(api_key)

def generate_code(user_input, self_improve, selected_file, num_attempts):
    output = ""
    num_attempts = int(num_attempts)
    if self_improve:
        with open(f"files_to_improve/{selected_file}", "r") as f:
            existing_code = f.read()

        for attempt in range(1, num_attempts + 1):
            gpt3_question = f"The current code is:\n```\n{existing_code}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Comment about the changes you are making."
            response = auto_coder.ask_gpt3(gpt3_question)
            update_filename = f"experiments/{selected_file}_update_{attempt}.py"
            auto_coder.save_generated_code(response, filename=update_filename)
            existing_code = response

            output += f"Improved code {attempt}:\n\n{response}\n\nLatest improved code has been saved as '{update_filename}'.\n\n"

    else:
        if user_input:
            gpt3_question = auto_coder.get_project_idea(user_input)
        else:
            gpt3_question = auto_coder.get_project_idea("")

        response = auto_coder.ask_gpt3(gpt3_question)
        file_number = auto_coder.save_generated_code(response)

        output += f"Generated code:\n\n{response}\n\nGenerated code has been saved as 'experiments/ex_{file_number}.py'.\n\n"

        for attempt in range(1, int(num_attempts) + 1):
            gpt3_question = f"The current code is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Comment about the changes you are making."
            response = auto_coder.ask_gpt3(gpt3_question)
            update_filename = f"experiments/ex_{file_number}_update_{attempt}.py"
            auto_coder.save_generated_code(response, filename=update_filename)

            output += f"Improved code {attempt}:\n\n{response}\n\nLatest improved code has been saved as '{update_filename}'.\n\n"

    return output

iface = gr.Interface(
    fn=generate_code,
    inputs=[
        gr.inputs.Textbox(label="Enter an idea for a Python project or leave it blank for a random suggestion"),
        gr.inputs.Checkbox(label="Check this box if you want to improve an existing file"),
        gr.inputs.Dropdown(choices=[f for f in os.listdir("files_to_improve") if f.endswith('.py')], label="Select a file to improve"),
        # Take in integer input for number of iterations
        gr.inputs.Number(label="Enter the number of iterations for improvement", default=1)
    ],
    outputs=gr.outputs.Textbox(label="Generated/Improved Code"),
    title="GPT-4 Auto Coder and Self Improver",
    description="Generate and improve Python code using GPT-4 Auto Coder.",
    allow_flagging=False, 

)

iface.launch()
