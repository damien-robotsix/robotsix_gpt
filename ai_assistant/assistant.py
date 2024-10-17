from openai import OpenAI
import os
import repo_chunker
import update_embedding
from embedding_search import search
from ai_assistant.assistant_functions import modify_chunk_tool, TaskInput
import json
import argparse

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

repo_chunker.main()
update_embedding.main()

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Process a request using the AI assistant.')

# Add arguments
parser.add_argument('-m', type=str, required=True, help='The message or prompt to process using the assistant.')

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
]

iterations = 0

for _, row in context.iterrows():
    line_start = row['line_start']
    line_end = row['line_end']
    file_path = row['file_path']
    with open(file_path, 'r') as file:
        lines = file.readlines()
        content = ''.join(
            lines[line_start - 1:line_end]).strip()
    messages.append({
        "role": "user",
        "content": json.dumps({
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "content": content
        })
    })
    iterations += 1
    if iterations > 5:
        break

response = client.chat.completions.create(
    messages=messages,
    model="gpt-4o-2024-08-06",
    tools  = [
        modify_chunk_tool
    ]
)


if response.choices[0].finish_reason == "tools_call":
    for tool in response.choices[0].message.tool_calls:
        task = TaskInput.model_construct(input_type=tool.function.name, parameters=tool.function.arguments)
        output = task.execute()
print(response.choices[0].message.content)