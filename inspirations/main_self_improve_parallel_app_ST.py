import streamlit as st
from main_self_improve_parallel_Class import GPT4AutoCoderSelfImprover
import os
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

def run_process(i, process_inputs, process_updates):
    process_folder = GPT4AutoCoderSelfImprover.create_process_folder(i + 1)
    GPT4AutoCoderSelfImprover.main(process_inputs, process_folder)
    return i, process_folder, process_inputs

def update_code_display(i, attempt, code):
    st.session_state.process_results[i]["code"][attempt] = code
    st.experimental_rerun()

st.title("GPT-4 Auto Coder and Self Improver")

num_processes = st.slider("How many processes do you want to start?", 1, 10, 1)

process_inputs_list = []
for i in range(num_processes):
    st.header(f"Process {i + 1}")
    process_inputs = {
        "user_input": st.text_input(f"Enter an idea for a Python project for process {i + 1} or leave it blank for a random suggestion:", key=f"user_input_{i}"),
        "self_improve": st.checkbox(f"Improve an existing file for process {i + 1}?", key=f"self_improve_{i}"),
        "selected_file": None,
        "num_improvements": st.slider(f"How many iterations of improvement would you like for process {i + 1}?", 0, 10, 1, key=f"num_improvements_{i}"),
    }

    if process_inputs["self_improve"]:
        files = [f for f in os.listdir("files_to_improve") if f.endswith('.py')]
        if not files:
            st.write("No files found in the 'files_to_improve' folder.")
        else:
            process_inputs["selected_file"] = st.selectbox(f"Choose a file to improve for process {i + 1}:", files, key=f"selected_file_{i}")
    
    process_inputs_list.append(process_inputs)

if st.button("Generate Code"):
    if "process_results" not in st.session_state:
        st.session_state.process_results = [{"code": {}} for _ in range(num_processes)]

    with ThreadPoolExecutor() as executor:
        process_updates = {i: update_code_display for i in range(num_processes)}
        process_results = list(executor.map(run_process, range(num_processes), process_inputs_list, [process_updates] * num_processes))

    for i, process_folder, process_inputs in process_results:
        st.header(f"Generated Code for Process {i + 1}")
        if process_inputs["self_improve"]:
            filename_prefix = os.path.splitext(os.path.basename(process_inputs["selected_file"]))[0]
        else:
            filename_prefix = "ex_1"

        # Display the original generated code
        original_code_path = f"files_to_improve/{filename_prefix}.py"
        if os.path.isfile(original_code_path):
            with open(original_code_path, "r") as file:
                original_code = file.read()
            st.code(original_code, language="python")
        else:
            st.write("Original code not found.")

elif "process_results" in st.session_state:
    for i, process_data in enumerate(st.session_state.process_results):
        st.header(f"Generated Code for Process {i + 1}")
        process_inputs = process_inputs_list[i]
        if process_inputs["self_improve"]:
            filename_prefix = os.path.splitext(os.path.basename(process_inputs["selected_file"]))[0]
        else:
            filename_prefix = "ex_1"

        # Display the original generated code
        original_code_path = f"{process_data['folder']}/{filename_prefix}.py"
        if os.path.isfile(original_code_path):
            with open(original_code_path, "r") as file:
                original_code = file.read()
            st.code(original_code, language="python")
        else:
            st.write("Original code not found.")

        # Display the improved code iterations
        for attempt, code in process_data["code"].items():
            st.write(f"**Improved Code (Iteration {attempt}):**")
            st.code(code, language="python")

