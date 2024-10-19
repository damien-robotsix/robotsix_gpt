from openai import OpenAI
import os
import repo_chunker
import update_embedding
from embedding_search import search
from ai_assistant.assistant_tools import modify_chunk_tool, TaskInput, create_file_tool
import json
import argparse

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

repo_chunker.main()
update_embedding.main()

# Initialize the argument parser
parser = argparse.ArgumentParser(
    description='Process a request using the AI assistant.')

# Add arguments
parser.add_argument('-m', type=str, required=True,
                    help='The message or prompt to process using the assistant.')

# Parse the arguments
args = parser.parse_args()

# Use the command line argument as the prompt
prompt = args.m

context = search(prompt)

messages = [
    {
        "role": "user",
        "content": prompt
    },
    {
        "role": "user",
        "content": "Some context that might help you is found below:"
    }
]

iterations = 0

for _, row in context.iterrows():
    line_start = row['line_start']
    line_end = row['line_end']
    file_path = row['file_path']
    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Append with line numbers
        lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
        content = ''.join(
            lines[line_start - 1:line_end]).strip()
    messages.append({
        "role": "user",
        "content": json.dumps({
            "file_path": file_path,
            "extracted_content": content
        })
    })
    iterations += 1
    print(file_path)
    print(line_start)
    print(line_end)
    print(content)
    if iterations > 6:
        break

response = client.chat.completions.create(
    messages=messages,
    model="gpt-4o-2024-08-06",
    tools=[
        modify_chunk_tool,
        create_file_tool
    ]
)

print("Finish")
print(response.choices[0].finish_reason)
print(response.choices[0])

if response.choices[0].finish_reason == 'tool_calls':
    for tool in response.choices[0].message.tool_calls:
        print(tool)
        task = TaskInput.model_construct(
            input_type=tool.function.name, parameters=tool.function.arguments)
        output = task.execute()
print(response.choices[0].message.content)
