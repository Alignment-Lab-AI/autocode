import streamlit as st
from main_self_improve_Class import GPT4AutoCoder
import os

st.set_page_config(page_title="GPT-4 Auto Coder", layout="wide")
st.title("GPT-4 Auto Coder and Self Improver")

# get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")
auto_coder = GPT4AutoCoder(api_key)

user_input = st.text_input("Enter an idea for a Python project or leave it blank for a random suggestion:")

self_improve = st.checkbox("Check this box if you want to improve an existing file")

if self_improve:
    files = [f for f in os.listdir("files_to_improve") if f.endswith('.py')]
    file_options = [f"Choose a file to improve"] + files
    selected_file = st.selectbox("Select a file to improve:", file_options)
    if selected_file != "Choose a file to improve":
        num_attempts = st.number_input("Enter the number of iterations for improvement:", min_value=0, value=1, step=1)
else:
    num_attempts = st.number_input("Enter the number of iterations for improvement:", min_value=0, value=1, step=1)

if st.button("Generate Code"):
    with st.spinner("Generating code..."):
        if self_improve and selected_file != "Choose a file to improve":
            with open(f"files_to_improve/{selected_file}", "r") as f:
                existing_code = f.read()

            for attempt in range(1, num_attempts + 1):
                gpt3_question = f"The current code is:\n```\n{existing_code}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Comment about the changes you are making."
                response = auto_coder.ask_gpt3(gpt3_question)
                update_filename = f"experiments/{selected_file}_update_{attempt}.py"
                auto_coder.save_generated_code(response, filename=update_filename)
                existing_code = response

                st.code(response, language="python")
                st.success(f"The latest improved code has been saved as '{update_filename}'.")

        else:
            if user_input:
                gpt3_question = auto_coder.get_project_idea(user_input)
            else:
                gpt3_question = auto_coder.get_project_idea("")

            response = auto_coder.ask_gpt3(gpt3_question)
            file_number = auto_coder.save_generated_code(response)

            st.code(response, language="python")
            st.success(f"The generated code has been saved as 'experiments/ex_{file_number}.py'.")

            for attempt in range(1, num_attempts + 1):
                gpt3_question = f"The current code is:\n```\n{response}\n``` Improve the following Python code (implement new ideas if necessary), including error catching and bug fixing. Write the entire code from scratch while implementing the improvements. Start the code block with a simple 'python' word. Comment about the changes you are making."
                response = auto_coder.ask_gpt3(gpt3_question)
                update_filename = f"experiments/ex_{file_number}_update_{attempt}.py"
                auto_coder.save_generated_code(response, filename=update_filename)
                st.code(response, language="python")
                st.success(f"The latest improved code has been saved as '{update_filename}'.")