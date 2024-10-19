import json
from openai import OpenAI
import os
from typing import List, Dict
from embedding_search import search
from assistant_tools import modify_chunk_tool, create_file_tool

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


class AssistantFSMFunctions:
    def __init__(self, client):
        self.client = client
        # Ensure the .ai_assistant directory exists
        self.log_file_path = os.path.join(
            '.ai_assistant', 'interaction_log.json')
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

    def generate_context(self, prompt: str) -> List[Dict]:
        context = search(prompt)
        formatted_context = []

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
            formatted_context.append({
                "role": "user",
                "content": json.dumps({
                    "file_path": file_path,
                    "extracted_content": content
                })
            })
            iterations += 1
            if iterations > 6:
                break

        return formatted_context

    def respond_to_prompt(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are an expert AI assistant. Your role is to help the user with their request concerning the current repository. Your answer should be concise and accurate. "
                "You might be asked to create code. In that case, you should act as a software engineer expert to solve the user's problem."
            },
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "user",
                "content": "Some context that might help you is found below:"
            }
        ]

        context = self.generate_context(prompt)

        messages = messages + context


        response = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o-2024-08-06",
            tools=[
                modify_chunk_tool,
                create_file_tool
            ]
        )

        # Log the interaction
        self.log_interaction(messages, response)

        return response

    def log_interaction(self, messages, response: str):
        with open(self.log_file_path, 'a') as log_file:
            json.dump(messages, log_file, indent=4)
            log_file.write('\n')
            json.dump(response.choices[0].message.content, log_file, indent=4)
            log_file.write('\n')
            if response.choices[0].finish_reason == 'tool_calls':
                for tool in response.choices[0].message.tool_calls:
                    json.dump(tool.function.name, log_file, indent=4)
            log_file.write('\n')
